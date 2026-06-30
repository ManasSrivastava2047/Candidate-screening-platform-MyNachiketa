const jdInput = document.getElementById("jdInput");
const saveJdBtn = document.getElementById("saveJdBtn");
const jdStatus = document.getElementById("jdStatus");

saveJdBtn.addEventListener("click", saveJd);

async function saveJd() {
  const jd = jdInput.value.trim();
  if (!jd) { setJdStatus("Please paste a job description.", "err"); return; }

  Pipeline.setLoading(2, true);
  try {
    const res = await fetch("/api/save-jd", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ jd }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Save failed");
    setJdStatus(`Saved (${data.length} chars)`, "ok");
    await Pipeline.refreshPipeline();
  } catch (e) {
    setJdStatus(e.message, "err");
  } finally {
    Pipeline.setLoading(2, false);
  }
}

function setJdStatus(msg, type) {
  jdStatus.textContent = msg;
  jdStatus.className = "status " + type;
}

fetch("/api/jd").then((r) => r.json()).then((d) => {
  if (d.jd) { jdInput.value = d.jd; setJdStatus(`Saved (${d.length} chars)`, "ok"); }
}).catch(() => {});
