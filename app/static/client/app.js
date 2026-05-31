const sessionId = "s001";
const deviceId = "glass001";
const origin = { lng: 116.2699, lat: 39.9991, coord_type: "gcj02" };

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
  baiduMap: document.querySelector("#baiduMap"),
  fallbackMap: document.querySelector("#fallbackMap"),
};

const api = {
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
  document.querySelectorAll(".view").forEach((view) => {
    view.classList.toggle("active", view.dataset.view === name);
  });
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.classList.toggle("active", tab.dataset.switch === name);
  });
}

function setNarration(text) {
  els.mainNarration.textContent = text || "没有返回内容。";
}

function setSuggestions(items = []) {
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
    els.fallbackMap.hidden = false;
    els.baiduMap.hidden = true;
    baiduMap = null;
    addEvent("map_ready", "百度地图 SDK 已加载，当前使用插画地图底图");
    return;
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
    `<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 48 48">
      <defs>
        <filter id="shadow" x="-30%" y="-30%" width="160%" height="160%">
          <feDropShadow dx="0" dy="5" stdDeviation="4" flood-color="#4d1511" flood-opacity=".28"/>
        </filter>
      </defs>
      <g filter="url(#shadow)">
        <path d="M24 4.5c4.6 5.1 9.9 5.1 15.9.2-2.2 7-.3 11.6 5.6 13.9-6.3 2.8-8.1 7.5-5.3 14.2-6.3-3.6-11.7-2.3-16.2 3.8-4.5-6.1-9.9-7.4-16.2-3.8 2.8-6.7 1-11.4-5.3-14.2 5.9-2.3 7.8-6.9 5.6-13.9 6 4.9 11.3 4.9 15.9-.2Z" fill="#8f2f26" stroke="#bd9550" stroke-width="2.4"/>
        <circle cx="24" cy="20.5" r="8.3" fill="#bd9550" opacity=".18"/>
        <path d="M15.2 21.8c3.9-5.5 13.7-5.5 17.6 0M17.8 27.1c4.4 3.1 8 3.1 12.4 0M24 28.2v12.3M19.5 35.2h9" fill="none" stroke="#fff5dc" stroke-width="2.2" stroke-linecap="round"/>
      </g>
    </svg>`,
    48,
  );
}

function destinationIcon() {
  return createSvgIcon(
    `<svg xmlns="http://www.w3.org/2000/svg" width="44" height="44" viewBox="0 0 44 44">
      <path d="M22 3.8c8.6 0 15.6 6.9 15.6 15.5 0 10.7-15.6 21-15.6 21S6.4 30 6.4 19.3C6.4 10.7 13.4 3.8 22 3.8Z" fill="#173f36" stroke="#bd9550" stroke-width="2.2"/>
      <path d="M13.7 20.8h16.6M16.2 17.8l5.8-4.4 5.8 4.4M17.4 20.8v6.8M26.6 20.8v6.8" fill="none" stroke="#fff5dc" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>`,
    44,
  );
}

function createMapLabel(text, offset = new baiduSdk.Size(18, -12)) {
  const label = new baiduSdk.Label(text, { offset });
  label.setStyle({
    color: "#5f1f1a",
    backgroundColor: "rgba(255, 248, 229, .92)",
    border: "1px solid #bd9550",
    borderRadius: "999px",
    padding: "4px 9px",
    fontFamily: '"SimSun", "Songti SC", serif',
    fontSize: "12px",
    boxShadow: "0 8px 18px rgba(76, 33, 22, .16)",
  });
  return label;
}

function drawCurrentPosition(point) {
  currentPoint = point;
  if (!baiduMap || !baiduSdk) return;
  if (activeRoute) {
    drawRoute(activeRoute, point);
    return;
  }
  baiduMap.clearOverlays();
  const marker = new baiduSdk.Marker(toBaiduPoint(point), { icon: currentLocationIcon() });
  marker.setLabel(createMapLabel("当前位置"));
  baiduMap.addOverlay(marker);
}

function drawRoute(route, movingPoint = currentPoint || origin) {
  if (!baiduMap || !baiduSdk || !route?.polyline?.length) return;
  baiduMap.clearOverlays();
  const points = route.polyline.map(toBaiduPoint);
  const line = new baiduSdk.Polyline(points, {
    strokeColor: "#8f2f26",
    strokeWeight: 7,
    strokeOpacity: 0.92,
  });
  baiduMap.addOverlay(line);

  const start = new baiduSdk.Marker(toBaiduPoint(movingPoint), { icon: currentLocationIcon() });
  start.setLabel(createMapLabel("当前位置"));
  baiduMap.addOverlay(start);

  const destinationPoint = points[points.length - 1];
  const destination = new baiduSdk.Marker(destinationPoint, { icon: destinationIcon() });
  destination.setLabel(createMapLabel(route.destination_name));
  baiduMap.addOverlay(destination);
  baiduMap.setViewport([toBaiduPoint(movingPoint), ...points], { margins: [72, 34, 116, 34] });
}

function connectWebSocket() {
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
  try {
    addEvent("action", label);
    await fn();
    switchView(nextView);
  } catch (error) {
    addEvent("error", error.message);
    setNarration(error.message);
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
  const message = data.actions[0]?.message || "已识别画面。";
  setNarration(message);
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
    setNarration(data.response_text);
    setSuggestions(data.suggested_questions || []);
    if (data.route) updateRoute(data.route);
  }, "guide");
});

document.querySelector("#clearEventsBtn")?.addEventListener("click", () => {
  els.eventList.innerHTML = "";
});

connectWebSocket();
initBaiduMap();
addEvent("ready", "手机客户端已加载");
