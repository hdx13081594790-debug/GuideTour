const adminState = { pois: [] };
const $ = (selector) => document.querySelector(selector);

async function requestJson(url, options = {}) {
  const response = await fetch(url, options);
  if (!response.ok) throw new Error(await response.text());
  return response.json();
}

function fillForm(poi) {
  $("#poiId").value = poi.id;
  $("#poiName").value = poi.name;
  $("#poiNameEn").value = poi.name_en;
  $("#poiTags").value = poi.tags.join(",");
  $("#poiX").value = poi.x;
  $("#poiY").value = poi.y;
  $("#poiSummary").value = poi.summary;
  $("#poiStory").value = poi.story;
}

function renderTable() {
  $("#adminCount").textContent = `${adminState.pois.length} 项`;
  $("#poiTable").innerHTML = adminState.pois
    .map(
      (poi) => `
        <div class="table-row">
          <div>
            <strong>${poi.name}</strong>
            <span>${poi.tags.join("、")} · ${poi.visit_minutes} 分钟</span>
          </div>
          <button class="button secondary" type="button" data-id="${poi.id}">编辑</button>
        </div>
      `,
    )
    .join("");
  $("#poiTable").querySelectorAll("button").forEach((button) => {
    button.addEventListener("click", () => {
      const poi = adminState.pois.find((item) => item.id === button.dataset.id);
      if (poi) fillForm(poi);
    });
  });
}

async function loadPois() {
  adminState.pois = await requestJson("/api/poi");
  renderTable();
  if (adminState.pois[0]) fillForm(adminState.pois[0]);
}

async function savePoi(event) {
  event.preventDefault();
  const payload = {
    id: $("#poiId").value.trim(),
    name: $("#poiName").value.trim(),
    name_en: $("#poiNameEn").value.trim(),
    x: Number($("#poiX").value),
    y: Number($("#poiY").value),
    tags: $("#poiTags")
      .value.split(",")
      .map((item) => item.trim())
      .filter(Boolean),
    open_time: "08:30-17:00",
    visit_minutes: 20,
    image_url: "",
    summary: $("#poiSummary").value.trim(),
    story: $("#poiStory").value.trim(),
  };
  $("#saveStatus").textContent = "保存中";
  try {
    await requestJson(`/api/admin/poi/${payload.id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    $("#saveStatus").textContent = "已保存";
    await loadPois();
  } catch (error) {
    $("#saveStatus").textContent = `保存失败：${error.message}`;
  }
}

$("#poiForm").addEventListener("submit", savePoi);
loadPois().catch((error) => {
  $("#poiTable").textContent = `加载失败：${error.message}`;
});
