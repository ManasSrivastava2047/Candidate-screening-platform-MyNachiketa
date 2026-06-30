const processBtn = document.getElementById("processResumesBtn");
const resumeStatus = document.getElementById("resumeStatus");

processBtn.addEventListener("click", processResumes);

async function processResumes() {
  Pipeline.setLoading(3, true);
  processBtn.disabled = true;
  try {
    const res = await fetch("/api/process-resumes", { method: "POST" });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Processing failed");
    const s = data.summary;
    setResumeStatus(`Done — ${s.ok} parsed, ${s.failed} failed, ${s.skipped} skipped`, s.failed ? "warn" : "ok");
    if (window.renderCandidates) window.renderCandidates(data.candidates);
    await Pipeline.refreshPipeline();
  } catch (e) {
    setResumeStatus(e.message, "err");
  } finally {
    processBtn.disabled = false;
    Pipeline.setLoading(3, false);
  }
}

function setResumeStatus(msg, type) {
  resumeStatus.textContent = msg;
  resumeStatus.className = "status " + type;
}
