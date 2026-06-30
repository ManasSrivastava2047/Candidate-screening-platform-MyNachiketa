const dropZone = document.getElementById("dropZone");
const fileInput = document.getElementById("fileInput");
const browseBtn = document.getElementById("browseBtn");
const status = document.getElementById("uploadStatus");
const tableBody = document.getElementById("tableBody");
const countEl = document.getElementById("count");
const clearBtn = document.getElementById("clearBtn");

browseBtn.addEventListener("click", () => { fileInput.value = ""; fileInput.click(); });
dropZone.addEventListener("click", () => { fileInput.value = ""; fileInput.click(); });
dropZone.addEventListener("dragover", (e) => { e.preventDefault(); dropZone.classList.add("over"); });
dropZone.addEventListener("dragleave", () => dropZone.classList.remove("over"));
dropZone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropZone.classList.remove("over");
  if (e.dataTransfer.files[0]) upload(e.dataTransfer.files[0]);
});
fileInput.addEventListener("change", () => {
  if (fileInput.files[0]) upload(fileInput.files[0]);
});
clearBtn.addEventListener("click", async () => {
  await fetch("/api/candidates", { method: "DELETE" });
  render([]);
  setStatus("Cleared.", "ok");
  Pipeline.refreshPipeline();
});

async function upload(file) {
  setStatus("Uploading…", "");
  Pipeline.setLoading(1, true);
  browseBtn.disabled = true;

  try {
    const form = new FormData();
    form.append("file", file);
    const res = await fetch("/api/upload", { method: "POST", body: form });
    const data = await res.json();
    if (!res.ok) throw new Error(data.errors?.join("; ") || data.error || "Upload failed");

    render(data.candidates);
    let msg = data.message;
    if (data.errors?.length) msg += ` (${data.errors.length} row(s) skipped)`;
    setStatus(msg, data.errors?.length ? "warn" : "ok");
    await Pipeline.refreshPipeline();
  } catch (e) {
    setStatus(e.message, "err");
  } finally {
    browseBtn.disabled = false;
    Pipeline.setLoading(1, false);
  }
}

function setStatus(msg, type) {
  status.textContent = msg;
  status.className = "status " + type;
}

function render(list) {
  countEl.textContent = list.length;
  clearBtn.hidden = list.length === 0;
  if (!list.length) {
    tableBody.innerHTML = '<tr><td colspan="8" class="empty">No candidates yet</td></tr>';
    return;
  }
  tableBody.innerHTML = list.map((c) => `
    <tr>
      <td>${c.s_no ?? ""}</td>
      <td><strong>${esc(c.name)}</strong><br><span class="sub-cell">${esc(c.email)}</span></td>
      <td class="mono">${fmtCgpa(c.cgpa)}</td>
      <td>${scoreCell(c.jd_score, c.jd_reasoning)}</td>
      <td>${scoreCell(c.project_score, c.project_reasoning)}</td>
      <td>${parseBadge(c)}</td>
      <td><span class="pill">${c.status || "applied"}</span></td>
      <td class="reasoning-cell">${reasoningCell(c)}</td>
    </tr>
  `).join("");
}

function fmtCgpa(v) { const n = Number(v); return isNaN(n) ? "—" : n.toFixed(2); }

function scoreCell(score, reasoning) {
  if (score == null) return '<span class="na">—</span>';
  const pct = (Number(score) * 100).toFixed(0);
  const cls = score >= 0.6 ? "score-high" : score >= 0.4 ? "score-mid" : "score-low";
  return `<span class="score ${cls}" title="${esc(reasoning || "")}">${pct}%</span>`;
}

function reasoningCell(c) {
  if (c.eval_status === "failed")
    return `<span class="eval-fail" title="${esc(c.eval_error || "")}">Eval failed</span>`;
  if (c.jd_reasoning) {
    const short = c.jd_reasoning.length > 80 ? c.jd_reasoning.slice(0, 80) + "…" : c.jd_reasoning;
    return `<span class="truncate" title="${esc((c.jd_reasoning || "") + "\n\n" + (c.project_reasoning || ""))}">${esc(short)}</span>`;
  }
  return '<span class="na">—</span>';
}

function parseBadge(c) {
  const st = c.resume_status;
  if (!st) return '<span class="parse pending">—</span>';
  return `<span class="parse ${st}" title="${esc(c.resume_error || "")}">${st === "ok" ? "OK" : st === "na" ? "NA" : "Failed"}</span>`;
}

function esc(s) { const d = document.createElement("div"); d.textContent = s ?? ""; return d.innerHTML; }

window.renderCandidates = render;

fetch("/api/candidates").then((r) => r.json()).then((d) => {
  if (d.candidates?.length) render(d.candidates);
}).catch(() => {});
