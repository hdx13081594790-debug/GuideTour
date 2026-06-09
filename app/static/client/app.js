const sessionId = "s001";
const deviceId = "glass001";
const origin = { lng: 116.2699, lat: 39.9991, coord_type: "gcj02" };

// 这个文件是手机端演示页面的“薄前端控制器”。
//
// 主要职责：
// 1. 绑定底部 tab、问答表单、导航按钮等 UI 事件；
// 2. 调用 FastAPI 后端接口；
// 3. 接收 WebSocket 实时事件；
// 4. 把后端返回的路线/回答/事件渲染到页面。
//
// 数据流示例：
// - 问答：chatForm submit -> POST /api/v1/agent/chat -> askAnswer 显示回答；
// - 导航：后端返回 route -> updateRoute() -> 百度地图画 polyline；
// - 实时：WebSocket message -> updateNavigationState()/setNarration()。

let currentTaskId = null;
let baiduMap = null;
let baiduSdk = null;
let currentPoint = null;
let activeRoute = null;

const els = {
  wsStatus: document.querySelector("#wsStatus"),
  headingValue: document.querySelector("#headingValue"),
  navStatus: document.querySelector("#navStatus"),
  distanceValue: document.querySelector("#distanceValue"),
  stepValue: document.querySelector("#stepValue"),
  mapDestination: document.querySelector("#mapDestination"),
  mainNarration: document.querySelector("#mainNarration"),
  suggestions: document.querySelector("#suggestions"),
  intentLabel: document.querySelector("#intentLabel"),
  eventList: document.querySelector("#eventList"),
  chatForm: document.querySelector("#chatForm"),
  chatInput: document.querySelector("#chatInput"),
  askAnswer: document.querySelector("#askAnswer"),
  baiduMap: document.querySelector("#baiduMap"),
  fallbackMap: document.querySelector("#fallbackMap"),
};

const api = {
  // 后端所有接口都返回 JSON；这里统一处理 response.ok 和错误消息。
  async get(path) {
    const response = await fetch(path);
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "请求失败");
    return data;
  },
  async post(path, body) {
    const response = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "请求失败");
    return data;
  },
};

function switchView(name) {
  // 页面不是多路由 SPA，只是通过 data-view 切换几个面板。
  document.querySelectorAll(".view").forEach((view) => {
    view.classList.toggle("active", view.dataset.view === name);
  });
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.classList.toggle("active", tab.dataset.switch === name);
  });
}

function setNarration(text) {
  if (els.mainNarration) {
    els.mainNarration.textContent = text || "没有返回内容。";
  }
}

function setSuggestions(items = []) {
  if (!els.suggestions) return;
  els.suggestions.innerHTML = "";
  items.forEach((item) => {
    const pill = document.createElement("button");
    pill.className = "suggestion";
    pill.type = "button";
    pill.textContent = item;
    pill.addEventListener("click", () => {
      els.chatInput.value = item;
      switchView("ask");
      els.chatForm.requestSubmit();
    });
    els.suggestions.appendChild(pill);
  });
}

function updateRoute(route) {
  // 后端 RouteResponse 是前端地图和底部导航状态的唯一数据来源。
  // 前端不重新计算路线，只负责展示 polyline、距离和 step。
  if (!route) return;
  currentTaskId = route.task_id;
  activeRoute = route;
  els.navStatus.textContent = "导航中";
  els.distanceValue.textContent = `${Math.round(route.distance_meters)}m`;
  els.stepValue.textContent = `1/${Math.max(route.steps.length, 1)}`;
  els.mapDestination.textContent = route.destination_name;
  setNarration(route.tts_text);
  drawRoute(route);
}

function updateNavigationState(state) {
  if (!state) return;
  currentTaskId = state.task_id;
  els.navStatus.textContent = state.status === "arrived" ? "已到达" : state.status === "cancelled" ? "已停止" : state.off_route ? "偏航" : "导航中";
  els.distanceValue.textContent = state.distance_to_destination_meters == null ? "--" : `${Math.round(state.distance_to_destination_meters)}m`;
  els.stepValue.textContent = `${state.current_step_index + 1}`;
  els.mapDestination.textContent = state.destination_name;
  if (state.last_location) {
    currentPoint = state.last_location;
    drawCurrentPosition(state.last_location);
  }
  if (state.last_instruction) setNarration(state.last_instruction);
}

function addEvent(type, detail) {
  if (!els.eventList) return;
  const item = document.createElement("li");
  item.className = "event-item";
  const title = document.createElement("strong");
  title.textContent = type;
  const body = document.createElement("span");
  body.textContent = detail;
  item.append(title, body);
  els.eventList.prepend(item);
  while (els.eventList.children.length > 22) {
    els.eventList.lastElementChild.remove();
  }
}

async function initBaiduMap() {
  // 浏览器端百度地图 AK 不写在前端源码里，而是从 /api/v1/config/map 获取。
  // 这样不同环境可以用不同 .env 配置。
  try {
    const config = await api.get("/api/v1/config/map");
    if (!config.baidu_browser_ak) {
      addEvent("map_fallback", "未配置浏览器端百度地图 AK");
      return;
    }
    await loadBaiduScript(config.baidu_browser_ak);
    if (!window.BMapGL) {
      addEvent("map_fallback", "百度地图 SDK 未加载");
      return;
    }
    baiduSdk = window.BMapGL;
    els.fallbackMap.hidden = true;
    els.baiduMap.hidden = false;
    document.querySelector(".map-hero")?.classList.remove("map-live");
    baiduMap = new baiduSdk.Map("baiduMap");
    const point = toBaiduPoint(origin);
    baiduMap.centerAndZoom(point, 16);
    baiduMap.enableScrollWheelZoom(true);
    if (typeof baiduMap.setTilt === "function") {
      baiduMap.setTilt(35);
    }
    drawCurrentPosition(origin);
    addEvent("map_ready", "百度地图底图已加载");
  } catch (error) {
    addEvent("map_fallback", error.message);
  }
}

function loadBaiduScript(ak) {
  if (window.BMapGL) return Promise.resolve();
  return new Promise((resolve, reject) => {
    window.__onBaiduMapLoaded = () => resolve();
    const script = document.createElement("script");
    script.src = `https://api.map.baidu.com/api?type=webgl&v=1.0&ak=${encodeURIComponent(ak)}&callback=__onBaiduMapLoaded`;
    script.onerror = () => reject(new Error("百度地图脚本加载失败"));
    document.head.appendChild(script);
  });
}

function toBaiduPoint(point) {
  return new baiduSdk.Point(point.lng, point.lat);
}

function createSvgIcon(svg, size = 44) {
  return new baiduSdk.Icon(`data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`, new baiduSdk.Size(size, size), {
    imageSize: new baiduSdk.Size(size, size),
    anchor: new baiduSdk.Size(size / 2, size / 2),
  });
}

function currentLocationIcon() {
  return createSvgIcon(
    `<svg xmlns="http://www.w3.org/2000/svg" width="42" height="42" viewBox="0 0 42 42">
      <circle cx="21" cy="21" r="10" fill="#A33A2C" stroke="#F7EEDC" stroke-width="3"/>
      <circle cx="21" cy="21" r="17" fill="none" stroke="#D7B56D" stroke-width="2" opacity=".45"/>
    </svg>`,
    42,
  );
}

function destinationIcon() {
  return createSvgIcon(
    `<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 40 40">
      <path d="M20 4c7 0 12.5 5.4 12.5 12.2 0 8.5-12.5 18.2-12.5 18.2S7.5 24.7 7.5 16.2C7.5 9.4 13 4 20 4Z" fill="#164B3E" stroke="#F7EEDC" stroke-width="2.4"/>
      <circle cx="20" cy="16" r="4" fill="#E7D2A0"/>
    </svg>`,
    40,
  );
}

function drawCurrentPosition(point) {
  currentPoint = point;
  if (!baiduMap || !baiduSdk) return;
  if (activeRoute) {
    drawRoute(activeRoute, point);
    return;
  }
  baiduMap.clearOverlays();
  baiduMap.addOverlay(new baiduSdk.Marker(toBaiduPoint(point), { icon: currentLocationIcon() }));
}

function drawRoute(route, movingPoint = currentPoint || origin) {
  if (!baiduMap || !baiduSdk || !route?.polyline?.length) return;
  baiduMap.clearOverlays();
  const points = route.polyline.map(toBaiduPoint);
  const line = new baiduSdk.Polyline(points, {
    strokeColor: "#7A2A22",
    strokeWeight: 7,
    strokeOpacity: 0.92,
  });
  baiduMap.addOverlay(line);
  baiduMap.addOverlay(new baiduSdk.Marker(toBaiduPoint(movingPoint), { icon: currentLocationIcon() }));
  baiduMap.addOverlay(new baiduSdk.Marker(points[points.length - 1], { icon: destinationIcon() }));
  baiduMap.setViewport([toBaiduPoint(movingPoint), ...points], { margins: [72, 34, 116, 34] });
}

function connectWebSocket() {
  // WebSocket 用 sessionId 分组。导航/位置/视觉事件都会从这里实时进入页面。
  const protocol = location.protocol === "https:" ? "wss" : "ws";
  const socket = new WebSocket(`${protocol}://${location.host}/api/v1/ws/${sessionId}`);

  socket.addEventListener("open", () => {
    els.wsStatus.classList.add("connected");
    els.wsStatus.classList.remove("error");
    els.wsStatus.querySelector("span:last-child").textContent = "实时在线";
  });

  socket.addEventListener("message", (event) => {
    const data = JSON.parse(event.data);
    addEvent(data.type, summarizeEvent(data));
    if (data.state) updateNavigationState(data.state);
    if (data.update) setNarration(data.update.tts_text);
    if (data.type === "location_updated") {
      els.headingValue.textContent = `${Math.round(data.location.heading || 0)}°`;
      drawCurrentPosition(data.location.location);
    }
    if (data.type === "vision_analyzed" && data.result?.actions?.length) {
      setNarration(data.result.actions[0].message);
    }
  });

  socket.addEventListener("close", () => {
    els.wsStatus.classList.remove("connected");
    els.wsStatus.classList.add("error");
    els.wsStatus.querySelector("span:last-child").textContent = "已断开";
    setTimeout(connectWebSocket, 1800);
  });
}

function summarizeEvent(data) {
  if (data.type === "connected") return `会话 ${data.session_id}`;
  if (data.type === "location_updated") return `位置 ${data.location.location.lng.toFixed(4)}, ${data.location.location.lat.toFixed(4)}`;
  if (data.type === "navigation_started") return `任务 ${data.task_id}`;
  if (data.type === "navigation_updated") return data.update.instruction;
  if (data.type === "navigation_stopped") return `任务 ${data.task_id}`;
  if (data.type === "vision_analyzed") return `${data.result.detected_pois.length} 个景点，${data.result.detected_gestures.length} 个手势`;
  if (data.type === "gesture_detected") return `${data.result.detected_gestures.length} 个手势`;
  return "事件已接收";
}

async function runAction(label, fn, nextView = "guide") {
  // 所有按钮动作都走这个包装器：
  // 先写事件日志，再执行异步请求，最后切换页面。
  // 如果出错，错误会显示到问答区/导览区，方便调试接口问题。
  try {
    addEvent("action", label);
    await fn();
    switchView(nextView);
  } catch (error) {
    addEvent("error", error.message);
    setNarration(error.message);

    if (els.askAnswer) {
      els.askAnswer.textContent = `请求失败：${error.message}`;
    }

    switchView("ask");
  }
}

document.querySelectorAll("[data-switch]").forEach((button) => {
  button.addEventListener("click", () => switchView(button.dataset.switch));
});

document.querySelector("#refreshLocationBtn")?.addEventListener("click", () => runAction("更新当前位置", async () => {
  const data = await api.post("/api/v1/location/update", {
    session_id: sessionId,
    device_id: deviceId,
    location: origin,
    heading: 85,
    pitch: 0,
    roll: 0,
    speed: 0.8,
    accuracy_meters: 5,
  });
  els.headingValue.textContent = `${Math.round(data.heading || 0)}°`;
  drawCurrentPosition(data.location);
}));

document.querySelector("#toiletBtn")?.addEventListener("click", () => runAction("最近厕所", async () => {
  const route = await api.post("/api/v1/navigation/nearest", {
    session_id: sessionId,
    origin,
    target_type: "toilet",
    radius_meters: 1000,
  });
  updateRoute(route);
}));

document.querySelector("#deheBtn")?.addEventListener("click", () => runAction("去德和园", async () => {
  const route = await api.post("/api/v1/navigation/route", {
    session_id: sessionId,
    origin,
    destination: { name: "德和园" },
    strategy: "walking",
    language: "zh",
  });
  updateRoute(route);
}));

document.querySelector("#explainBtn")?.addEventListener("click", () => runAction("讲解附近", async () => {
  const data = await api.post("/api/v1/agent/explain-nearby", {
    session_id: sessionId,
    device_id: deviceId,
    location: { lng: 116.2728, lat: 39.99955, coord_type: "gcj02" },
    heading: 90,
    language: "zh",
    style: "normal",
    accuracy_meters: 5,
  });
  setNarration(data.explanation);
  setSuggestions(data.suggested_questions);
  els.mapDestination.textContent = data.poi_name || "附近景点";
}));

document.querySelector("#ragBtn")?.addEventListener("click", () => runAction("RAG 追问", async () => {
  const data = await api.post("/api/v1/rag/answer", {
    query: "这个建筑为什么有三层？",
    poi_id: 2,
  });
  setNarration(data.answer);
}, "guide"));

document.querySelector("#gestureBtn")?.addEventListener("click", () => runAction("V 字拍照", async () => {
  const data = await api.post("/api/v1/vision/analyze-frames", {
    session_id: sessionId,
    device_id: deviceId,
    frame_ids: ["demo-frame"],
    mock_gesture: "take_photo",
  });
  setNarration(data.actions[0]?.message || "已识别画面。");
}, "guide"));

document.querySelector("#wakeQuestionBtn")?.addEventListener("click", () => {
  els.chatInput.value = "这个建筑有什么故事？";
  switchView("ask");
});

document.querySelector("#stopBtn")?.addEventListener("click", () => runAction("停止导航", async () => {
  if (!currentTaskId) {
    setNarration("当前没有正在进行的导航。");
    return;
  }
  await api.post("/api/v1/navigation/stop", { session_id: sessionId, task_id: currentTaskId });
  els.navStatus.textContent = "已停止";
}));

els.chatForm.addEventListener("submit", (event) => {
  // 问答输入框的数据流：
  // 用户文本 -> /api/v1/agent/chat -> DeepSeek Agent 决策
  // -> 如果是聊天，显示 response_text；如果是导航，额外 updateRoute()。
  event.preventDefault();

  runAction("对话请求", async () => {
    const data = await api.post("/api/v1/agent/chat", {
      session_id: sessionId,
      device_id: deviceId,
      text: els.chatInput.value,
      location: origin,
      heading: 85,
      language: "zh",
      current_poi_id: 2,
    });

    els.intentLabel.textContent = `intent: ${data.intent}`;

    if (els.askAnswer) {
      els.askAnswer.textContent = data.response_text;
    }

    setNarration(data.response_text);
    setSuggestions(data.suggested_questions || []);

    if (
      data.route &&
      ["NAVIGATE_TO_POI", "NAVIGATE_NEAREST_SERVICE"].includes(data.intent)
    ) {
      updateRoute(data.route);
    }
  }, "ask");
});

document.querySelector("#clearEventsBtn")?.addEventListener("click", () => {
  els.eventList.innerHTML = "";
});

connectWebSocket();
initBaiduMap();
addEvent("ready", "手机客户端已加载");
