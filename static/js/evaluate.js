const evaluateBtn = document.getElementById("evaluateBtn");
const evaluateStatus = document.getElementById("evaluateStatus");

evaluateBtn.addEventListener("click", runEvaluate);

async function runEvaluate() {
  Pipeline.setLoading(4, true);
  evaluateBtn.disabled = true;
  try {
    const res = await fetch("/api/evaluate", { method: "POST" });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Evaluation failed");
    const s = data.summary;
    let msg = `Done — ${s.ok} evaluated` + (s.failed ? `, ${s.failed} failed` : "");
    if (data.errors?.length) msg += `. ${data.errors[0]}`;
    setEvalStatus(msg, s.failed ? "warn" : "ok");
    if (window.renderCandidates) window.renderCandidates(data.candidates);
    await Pipeline.refreshPipeline();
  } catch (e) {
    setEvalStatus(e.message, "err");
  } finally {
    evaluateBtn.disabled = false;
    Pipeline.setLoading(4, false);
  }
}

function setEvalStatus(msg, type) {
  evaluateStatus.textContent = msg;
  evaluateStatus.className = "status " + type;
}
