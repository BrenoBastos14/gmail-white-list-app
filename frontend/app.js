const apiInput = document.getElementById("api-url");
const fileInput = document.getElementById("file-input");
const fileLabelText = document.getElementById("file-label-text");
const analyzeBtn = document.getElementById("analyze-btn");
const statusEl = document.getElementById("status");
const resultsEl = document.getElementById("results");

const scoreEl = document.getElementById("score");
const durationEl = document.getElementById("duration");
const verticesEl = document.getElementById("vertices");
const peaksEl = document.getElementById("peaks");
let chart = null;

const savedApi = localStorage.getItem("tribev2-api-url");
if (savedApi) apiInput.value = savedApi;
apiInput.addEventListener("change", () => {
  localStorage.setItem("tribev2-api-url", apiInput.value.trim());
});

function refreshButton() {
  analyzeBtn.disabled = !(apiInput.value.trim() && fileInput.files[0]);
}
apiInput.addEventListener("input", refreshButton);
fileInput.addEventListener("change", () => {
  const f = fileInput.files[0];
  fileLabelText.textContent = f
    ? `${f.name} (${(f.size / 1024 / 1024).toFixed(1)} MB)`
    : "Escolher vídeo (.mp4, .mov, .webm)";
  refreshButton();
});

function setStatus(text, kind = "") {
  statusEl.textContent = text;
  statusEl.className = "status" + (kind ? " " + kind : "");
}

analyzeBtn.addEventListener("click", async () => {
  const api = apiInput.value.trim().replace(/\/$/, "");
  const file = fileInput.files[0];
  if (!api || !file) return;

  analyzeBtn.disabled = true;
  resultsEl.classList.add("hidden");
  setStatus("Enviando vídeo e rodando TRIBE v2… isso leva alguns minutos.");

  const form = new FormData();
  form.append("video", file);

  try {
    const resp = await fetch(`${api}/predict`, { method: "POST", body: form });
    if (!resp.ok) {
      const errText = await resp.text();
      throw new Error(`HTTP ${resp.status}: ${errText}`);
    }
    const data = await resp.json();
    renderResults(data);
    setStatus("Análise concluída.", "success");
  } catch (err) {
    setStatus(`Erro: ${err.message}`, "error");
  } finally {
    analyzeBtn.disabled = false;
  }
});

function renderResults(data) {
  resultsEl.classList.remove("hidden");
  scoreEl.textContent = data.score.toFixed(1);
  durationEl.textContent = data.duration_s;
  verticesEl.textContent = data.n_vertices.toLocaleString();

  peaksEl.innerHTML = "";
  for (const s of data.peak_seconds) {
    const li = document.createElement("li");
    li.textContent = `t = ${s}s · engajamento ${data.curve[s].toFixed(1)}`;
    peaksEl.appendChild(li);
  }

  const ctx = document.getElementById("curve").getContext("2d");
  if (chart) chart.destroy();
  chart = new Chart(ctx, {
    type: "line",
    data: {
      labels: data.curve.map((_, i) => i),
      datasets: [
        {
          label: "Engajamento neural predito",
          data: data.curve,
          borderColor: "#58a6ff",
          backgroundColor: "rgba(88,166,255,0.15)",
          fill: true,
          tension: 0.25,
          pointRadius: 0,
        },
      ],
    },
    options: {
      responsive: true,
      scales: {
        x: { title: { display: true, text: "tempo (s)" }, ticks: { color: "#8b949e" } },
        y: { title: { display: true, text: "score 0–100" }, min: 0, max: 100, ticks: { color: "#8b949e" } },
      },
      plugins: { legend: { labels: { color: "#e6edf3" } } },
    },
  });
}
