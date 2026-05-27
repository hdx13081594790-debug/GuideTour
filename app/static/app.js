const state = {
  pois: [],
  sessionId: `demo-${Date.now()}`,
  language: "zh",
  currentPoiId: null,
};

const $ = (selector) => document.querySelector(selector);

async function requestJson(url, options = {}) {
  const response = await fetch(url, options);
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed: ${response.status}`);
  }
  return response.json();
}

function setLoading(node, text = "正在处理") {
  node.innerHTML = `<div class="loading" aria-label="${text}"></div>`;
}

function renderPins() {
  const mapPins = $("#mapPins");
  mapPins.innerHTML = state.pois
    .map(
      (poi) =>
        `<button class="pin" style="left:${poi.x}%; top:${poi.y}%;" data-poi="${poi.id}" title="${poi.name}"><span>${poi.name}</span></button>`,
    )
    .join("");
  mapPins.querySelectorAll(".pin").forEach((pin) => {
    pin.addEventListener("click", () => {
      $("#currentPoi").value = pin.dataset.poi;
      setCurrentPoi(pin.dataset.poi);
    });
  });
}

function renderPoiSelect() {
  const select = $("#currentPoi");
  select.innerHTML = state.pois.map((poi) => `<option value="${poi.id}">${poi.name}</option>`).join("");
  select.addEventListener("change", () => setCurrentPoi(select.value));
  setCurrentPoi(state.pois[0]?.id);
}

function setCurrentPoi(poiId) {
  state.currentPoiId = poiId;
  const poi = state.pois.find((item) => item.id === poiId);
  if (!poi) return;
  $("#poiDetail").innerHTML = `
    <h3>${poi.name}</h3>
    <p>${poi.summary}</p>
    <div class="tag-row">${poi.tags.map((tag) => `<span class="tag">${tag}</span>`).join("")}</div>
    <p><strong>建议停留：</strong>${poi.visit_minutes} 分钟</p>
  `;
}

function appendMessage(role, content, meta = "") {
  const log = $("#chatLog");
  const item = document.createElement("div");
  item.className = `message ${role}`;
  item.innerHTML = `${content}${meta ? `<small>${meta}</small>` : ""}`;
  log.appendChild(item);
  log.scrollTop = log.scrollHeight;
}

async function sendChat(message) {
  const value = message || $("#chatInput").value.trim();
  if (!value) return;
  appendMessage("user", value);
  $("#chatInput").value = "";
  appendMessage("assistant", '<div class="loading"></div>');
  const loading = $("#chatLog .message.assistant:last-child");
  try {
    const data = await requestJson("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: state.sessionId,
        message: value,
        language: state.language,
        current_poi_id: state.currentPoiId,
      }),
    });
    state.language = data.language;
    $("#languageBadge").textContent = data.language === "en" ? "English" : data.language === "ja" ? "日本語" : "中文";
    loading.innerHTML = `${data.answer}<small>意图：${data.intent} · 引用：${data.citations.map((item) => item.title).join("、") || "无"}</small>`;
  } catch (error) {
    loading.innerHTML = `请求失败：${error.message}`;
  }
}

async function handleAudio(file) {
  if (!file) return;
  const form = new FormData();
  form.append("file", file);
  appendMessage("user", `上传语音文件：${file.name}`);
  try {
    const data = await requestJson("/api/asr", { method: "POST", body: form });
    state.language = data.language;
    appendMessage("assistant", `识别文本：${data.transcript}`, data.note);
    await sendChat(data.transcript);
  } catch (error) {
    appendMessage("assistant", `语音识别失败：${error.message}`);
  }
}

async function recommendRoute() {
  const result = $("#routeResult");
  setLoading(result);
  const interests = $("#interests")
    .value.split(",")
    .map((item) => item.trim())
    .filter(Boolean);
  try {
    const data = await requestJson("/api/route/recommend", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        start_poi_id: state.currentPoiId,
        duration_minutes: Number($("#duration").value),
        interests,
      }),
    });
    result.innerHTML = `
      <p><strong>${data.narrative}</strong></p>
      ${data.stops
        .map(
          (stop) => `
            <div class="route-stop">
              <strong>${stop.name}</strong>
              <span>第 ${stop.arrive_after_minutes} 分钟抵达，停留 ${stop.stay_minutes} 分钟</span>
              <p>${stop.summary}</p>
            </div>
          `,
        )
        .join("")}
    `;
  } catch (error) {
    result.innerHTML = `路线生成失败：${error.message}`;
  }
}

async function handleImage(file) {
  if (!file) return;
  const result = $("#visionResult");
  setLoading(result);
  const form = new FormData();
  form.append("file", file);
  form.append("language", state.language);
  form.append("current_poi_id", state.currentPoiId || "");
  try {
    const data = await requestJson("/api/vision/recognize", { method: "POST", body: form });
    result.innerHTML = `
      <p><strong>${data.explanation}</strong></p>
      ${data.candidates
        .map(
          (candidate) => `
            <div class="candidate">
              <strong>${candidate.name} · ${(candidate.confidence * 100).toFixed(0)}%</strong>
              <p>${candidate.summary}</p>
            </div>
          `,
        )
        .join("")}
    `;
    appendMessage("assistant", data.explanation, "来自目标识别");
  } catch (error) {
    result.innerHTML = `识别失败：${error.message}`;
  }
}

async function boot() {
  state.pois = await requestJson("/api/poi");
  renderPins();
  renderPoiSelect();
  appendMessage("assistant", "你好，我是颐和园智慧导览 demo。你可以问景点历史、请求路线，或上传一张照片做识别讲解。");
  $("#sendChat").addEventListener("click", () => sendChat());
  $("#chatInput").addEventListener("keydown", (event) => {
    if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) sendChat();
  });
  $("#audioFile").addEventListener("change", (event) => handleAudio(event.target.files[0]));
  $("#recommendRoute").addEventListener("click", recommendRoute);
  $("#imageFile").addEventListener("change", (event) => handleImage(event.target.files[0]));
}

boot().catch((error) => {
  document.body.innerHTML = `<main class="app-shell"><section class="panel">启动失败：${error.message}</section></main>`;
});
