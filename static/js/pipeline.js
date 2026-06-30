/** Loading spinners + phase status badges only. All steps always usable. */
const Pipeline = {
  state: {
    step1_upload: false,
    step2_jd: false,
    step3_resumes: false,
    step4_evaluate: false,
  },
};

function setLoading(step, on, label) {
  const loader = document.getElementById(`loader${step}`);
  if (!loader) return;
  if (label) {
    const span = loader.querySelector("span");
    if (span) span.textContent = label;
  }
  loader.classList.toggle("hidden", !on);
}

function updatePhasePills() {
  const s = Pipeline.state;
  const keys = ["step1_upload", "step2_jd", "step3_resumes", "step4_evaluate"];
  document.querySelectorAll(".phase").forEach((pill) => {
    const n = Number(pill.dataset.phase);
    const key = keys[n - 1];
    pill.classList.remove("done", "active");
    if (s[key]) pill.classList.add("done");
    else pill.classList.add("active");
  });
}

async function refreshPipeline() {
  try {
    const res = await fetch("/api/pipeline");
    if (res.ok) {
      Pipeline.state = await res.json();
      updatePhasePills();
    }
  } catch (e) {
    console.warn("pipeline:", e);
  }
  return Pipeline.state;
}

window.Pipeline = { setLoading, refreshPipeline };

document.addEventListener("DOMContentLoaded", () => refreshPipeline());
