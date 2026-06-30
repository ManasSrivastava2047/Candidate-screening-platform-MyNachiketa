/* Visl Recruit — all UI logic in one file */
(function () {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const TOTAL_STEPS = 14;

  let currentStep = 1;
  const completedSteps = new Set();
  let cachedList = [];

  function esc(s) {
    const d = document.createElement("div");
    d.textContent = s ?? "";
    return d.innerHTML;
  }

  function setStatus(el, msg, type) {
    if (!el) return;
    el.textContent = msg;
    el.className = "status " + (type || "");
  }

  function setLoading(step, on) {
    const loader = $("loader" + step);
    if (loader) loader.classList.toggle("hidden", !on);
  }

  function canGoToStep(n) {
    if (n < 1 || n > TOTAL_STEPS) return false;
    for (let i = 1; i < n; i++) {
      if (!completedSteps.has(i)) return false;
    }
    return true;
  }

  function goToStep(n) {
    if (!canGoToStep(n)) return;
    currentStep = n;
    document.querySelectorAll(".step-panel").forEach((el) => {
      el.classList.toggle("active", Number(el.dataset.step) === n);
    });
    updateStepNav();
  }

  function updateStepNav() {
    document.querySelectorAll(".step-tab").forEach((btn) => {
      const step = Number(btn.dataset.step);
      btn.classList.toggle("active", step === currentStep);
      btn.classList.toggle("done", completedSteps.has(step));
      btn.disabled = !canGoToStep(step);
    });
    document.querySelectorAll(".step-connector").forEach((conn, i) => {
      conn.classList.toggle("done", completedSteps.has(i + 1));
    });
  }

  function completeStep(n, advance) {
    if (advance === undefined) advance = true;
    completedSteps.add(n);
    updateStepNav();
    if (advance && n < TOTAL_STEPS) {
      setTimeout(() => goToStep(n + 1), 450);
    }
  }

  function syncFromPipeline(pipe) {
    if (!pipe) return;
    if (pipe.step1_upload) completedSteps.add(1);
    if (pipe.step2_jd) completedSteps.add(2);
    if (pipe.step3_resumes) completedSteps.add(3);
    if (pipe.step4_evaluate) completedSteps.add(4);
    if (pipe.step5_github) completedSteps.add(5);
    if (pipe.step6_academic) completedSteps.add(6);
    if (pipe.step7_score) completedSteps.add(7);
    if (pipe.step8_shortlist) completedSteps.add(8);
    if (pipe.step9_test_emails) completedSteps.add(9);
    if (pipe.step10_test_results) completedSteps.add(10);
    if (pipe.step11_rescore) completedSteps.add(11);
    if (pipe.step12_google) completedSteps.add(12);
    if (pipe.step13_schedule) completedSteps.add(13);
    if (pipe.step14_interview_emails) completedSteps.add(14);

    let target = TOTAL_STEPS;
    for (let i = 1; i <= TOTAL_STEPS; i++) {
      if (!completedSteps.has(i)) {
        target = i;
        break;
      }
    }
    goToStep(target);
  }

  function fmtCgpa(v) {
    const n = Number(v);
    return isNaN(n) ? "—" : n.toFixed(2);
  }

  function fmt(val) {
    if (!val || val === "NA") return '<span class="na">NA</span>';
    return `<span class="truncate" title="${esc(val)}">${esc(val.length > 50 ? val.slice(0, 50) + "…" : val)}</span>`;
  }

  function linkOrNa(val) {
    if (!val || val === "NA") return '<span class="na">NA</span>';
    return `<a href="${esc(val)}" target="_blank" rel="noopener">Link</a>`;
  }

  function scoreCell(score, reasoning) {
    if (score == null) return '<span class="na">—</span>';
    const pct = (Number(score) * 100).toFixed(0);
    const cls = score >= 0.6 ? "score-high" : score >= 0.4 ? "score-mid" : "score-low";
    return `<span class="score ${cls}" title="${esc(reasoning || "")}">${pct}%</span>`;
  }

  function testScoreTip(c) {
    if (c.test_la == null) return "";
    return `LA: ${c.test_la}% · Code: ${c.test_code}%`;
  }

  function testScoreCell(c) {
    if (c.test_score != null) {
      return scoreCell(c.test_score, testScoreTip(c));
    }
    return '<span class="na">—</span>';
  }

  function hasRemarks(c) {
    return c.eval_status === "failed" || c.jd_reasoning || c.project_reasoning
      || c.github_reasoning || c.academic_reasoning;
  }

  function buildRemarksHtml(c) {
    if (c.eval_status === "failed") {
      return `<p class="eval-fail">${esc(c.eval_error || "Eval failed")}</p>`;
    }
    const blocks = [];
    if (c.jd_reasoning) {
      blocks.push(`<div class="reason-block"><strong>JD</strong>${esc(c.jd_reasoning)}</div>`);
    }
    if (c.project_reasoning) {
      blocks.push(`<div class="reason-block"><strong>Project</strong>${esc(c.project_reasoning)}</div>`);
    }
    if (c.github_reasoning) {
      blocks.push(`<div class="reason-block"><strong>GitHub</strong>${esc(c.github_reasoning)}</div>`);
    }
    if (c.academic_reasoning) {
      blocks.push(`<div class="reason-block"><strong>Academic</strong>${esc(c.academic_reasoning)}</div>`);
    }
    return `<div class="reasoning-text">${blocks.join("")}</div>`;
  }

  function remarksCell(c, idx) {
    if (!hasRemarks(c)) return '<span class="na">—</span>';
    return `<button type="button" class="remarks-link" data-idx="${idx}">View remarks</button>`;
  }

  function closeRemarksPopover() {
    const pop = $("remarksPopover");
    if (pop) pop.classList.add("hidden");
  }

  function openRemarksPopover(anchor, c) {
    const pop = $("remarksPopover");
    if (!pop) return;
    $("remarksTitle").textContent = `${c.name} — Remarks`;
    $("remarksBody").innerHTML = buildRemarksHtml(c);
    pop.classList.remove("hidden");
    const rect = anchor.getBoundingClientRect();
    const popW = Math.min(440, window.innerWidth - 32);
    let left = rect.left;
    let top = rect.bottom + 8;
    if (left + popW > window.innerWidth - 16) left = window.innerWidth - popW - 16;
    if (top + 280 > window.innerHeight) top = Math.max(8, rect.top - 288);
    pop.style.width = popW + "px";
    pop.style.left = Math.max(8, left) + "px";
    pop.style.top = top + "px";
  }

  function rankCell(c) {
    if (c.rank == null) return '<span class="na">—</span>';
    const cls = c.rank <= 3 ? `rank-${c.rank}` : "";
    return `<span class="rank-badge ${cls}">#${c.rank}</span>`;
  }

  function statusPill(c) {
    const st = c.status || "applied";
    let cls = "pill";
    if (st === "shortlisted") cls += " shortlisted";
    if (st === "test_sent") cls += " test-sent";
    if (st === "interview") cls += " interview";
    let title = "";
    if (c.interview_reason) title = c.interview_reason;
    else if (c.shortlist_reason) title = c.shortlist_reason;
    if (c.meet_link) title = (title ? title + " · " : "") + `Meet: ${c.meet_link}`;
    if (c.interview_start) title = (title ? title + " · " : "") + `Slot: ${c.interview_start}`;
    if (c.test_email_error) title = c.test_email_error;
    if (c.interview_email_error) title = c.interview_email_error;
    const titleAttr = title ? ` title="${esc(title)}"` : "";
    return `<span class="${cls}"${titleAttr}>${esc(st.replace(/_/g, " "))}</span>`;
  }

  function parseBadge(c) {
    const st = c.resume_status;
    if (!st) return '<span class="parse pending">—</span>';
    const lbl = st === "ok" ? "OK" : st === "na" ? "NA" : "Failed";
    return `<span class="parse ${st}" title="${esc(c.resume_error || "")}">${lbl}</span>`;
  }

  function render(list) {
    const tableBody = $("tableBody");
    const countEl = $("count");
    const clearBtn = $("clearBtn");
    if (!tableBody) return;

    cachedList = list;
    closeRemarksPopover();

    countEl.textContent = list.length;
    clearBtn.hidden = list.length === 0;

    if (!list.length) {
      tableBody.innerHTML = '<tr><td colspan="20" class="empty">No candidates yet</td></tr>';
      return;
    }

    tableBody.innerHTML = list.map((c, idx) => `
      <tr>
        <td>${c.s_no ?? ""}</td>
        <td>${rankCell(c)}</td>
        <td><strong>${esc(c.name)}</strong></td>
        <td>${esc(c.email)}</td>
        <td>${esc(c.college)}</td>
        <td>${esc(c.branch)}</td>
        <td class="mono">${fmtCgpa(c.cgpa)}</td>
        <td>${fmt(c.best_ai_project)}</td>
        <td>${fmt(c.research_work)}</td>
        <td>${linkOrNa(c.github)}</td>
        <td>${linkOrNa(c.resume)}</td>
        <td>${parseBadge(c)}</td>
        <td>${scoreCell(c.jd_score, c.jd_reasoning)}</td>
        <td>${scoreCell(c.project_score, c.project_reasoning)}</td>
        <td>${scoreCell(c.github_score, c.github_reasoning)}</td>
        <td>${scoreCell(c.cgpa_score, c.academic_reasoning)}</td>
        <td>${testScoreCell(c)}</td>
        <td>${scoreCell(c.composite_score, c.composite_breakdown)}</td>
        <td>${statusPill(c)}</td>
        <td class="reasoning-cell">${remarksCell(c, idx)}</td>
      </tr>
    `).join("");
  }

  async function api(url, opts) {
    const res = await fetch(url, { credentials: "same-origin", ...opts });
    let data;
    try { data = await res.json(); } catch { data = {}; }
    if (!res.ok) throw new Error(data.error || data.errors?.join("; ") || `Request failed (${res.status})`);
    return data;
  }

  async function upload(file) {
    const status = $("uploadStatus");
    const browseBtn = $("browseBtn");
    setStatus(status, "Uploading…", "");
    setLoading(1, true);
    browseBtn.disabled = true;

    try {
      const form = new FormData();
      form.append("file", file);
      const data = await api("/api/upload", { method: "POST", body: form });
      render(data.candidates);
      let msg = data.message;
      if (data.errors?.length) msg += ` (${data.errors.length} skipped)`;
      setStatus(status, msg, data.errors?.length ? "warn" : "ok");
      if (data.candidates?.length) completeStep(1);
    } catch (e) {
      setStatus(status, e.message, "err");
    } finally {
      browseBtn.disabled = false;
      setLoading(1, false);
    }
  }

  async function saveJd() {
    const jd = $("jdInput").value.trim();
    const jdStatus = $("jdStatus");
    if (!jd) { setStatus(jdStatus, "Paste a job description first.", "err"); return; }

    setLoading(2, true);
    try {
      const data = await api("/api/save-jd", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ jd }),
      });
      setStatus(jdStatus, `Saved (${data.length} chars)`, "ok");
      completeStep(2);
    } catch (e) {
      setStatus(jdStatus, e.message, "err");
    } finally {
      setLoading(2, false);
    }
  }

  async function processResumes() {
    const resumeStatus = $("resumeStatus");
    const btn = $("processResumesBtn");
    setLoading(3, true);
    btn.disabled = true;
    try {
      const data = await api("/api/process-resumes", { method: "POST" });
      const s = data.summary;
      setStatus(resumeStatus, `Done — ${s.ok} OK, ${s.failed} failed, ${s.skipped} skipped`, s.failed ? "warn" : "ok");
      render(data.candidates);
      completeStep(3);
    } catch (e) {
      setStatus(resumeStatus, e.message, "err");
    } finally {
      btn.disabled = false;
      setLoading(3, false);
    }
  }

  async function runEvaluate() {
    const evaluateStatus = $("evaluateStatus");
    const btn = $("evaluateBtn");
    setLoading(4, true);
    btn.disabled = true;
    try {
      const data = await api("/api/evaluate", { method: "POST" });
      const s = data.summary;
      let msg = `Done — ${s.ok} evaluated` + (s.failed ? `, ${s.failed} failed` : "");
      if (data.errors?.length) msg += `. ${data.errors[0]}`;
      setStatus(evaluateStatus, msg, s.failed ? "warn" : "ok");
      render(data.candidates);
      completeStep(4);
    } catch (e) {
      setStatus(evaluateStatus, e.message, "err");
    } finally {
      btn.disabled = false;
      setLoading(4, false);
    }
  }

  async function runGithub() {
    const githubStatus = $("githubStatus");
    const btn = $("githubBtn");
    setLoading(5, true);
    btn.disabled = true;
    try {
      const data = await api("/api/github", { method: "POST" });
      const s = data.summary;
      let msg = `Done — ${s.ok} analyzed`;
      if (s.skipped) msg += `, ${s.skipped} skipped`;
      if (s.failed) msg += `, ${s.failed} failed`;
      if (data.errors?.length) msg += `. ${data.errors[0]}`;
      setStatus(githubStatus, msg, s.failed ? "warn" : "ok");
      render(data.candidates);
      completeStep(5);
    } catch (e) {
      setStatus(githubStatus, e.message, "err");
    } finally {
      btn.disabled = false;
      setLoading(5, false);
    }
  }

  async function runAcademic() {
    const academicStatus = $("academicStatus");
    const btn = $("academicBtn");
    setLoading(6, true);
    btn.disabled = true;
    try {
      const data = await api("/api/academic-score", { method: "POST" });
      const s = data.summary;
      let msg = `Done — ${s.ok} scored`;
      if (s.failed) msg += `, ${s.failed} failed`;
      if (data.errors?.length) msg += `. ${data.errors[0]}`;
      setStatus(academicStatus, msg, s.failed ? "warn" : "ok");
      render(data.candidates);
      completeStep(6);
    } catch (e) {
      setStatus(academicStatus, e.message, "err");
    } finally {
      btn.disabled = false;
      setLoading(6, false);
    }
  }

  async function runScore() {
    const scoreStatus = $("scoreStatus");
    const btn = $("scoreBtn");
    setLoading(7, true);
    btn.disabled = true;
    try {
      const data = await api("/api/score", { method: "POST" });
      let msg = data.message;
      if (data.top_candidate) {
        msg += ` — Top: ${data.top_candidate} (${(data.top_score * 100).toFixed(0)}%)`;
      }
      if (data.warnings?.length) {
        msg += `. Note: missing ${data.warnings.join(", ")} (treated as 0).`;
      }
      setStatus(scoreStatus, msg, data.warnings?.length ? "warn" : "ok");
      render(data.candidates);
      completeStep(7);
    } catch (e) {
      setStatus(scoreStatus, e.message, "err");
    } finally {
      btn.disabled = false;
      setLoading(7, false);
    }
  }

  async function runShortlist() {
    const shortlistStatus = $("shortlistStatus");
    const btn = $("shortlistBtn");
    setLoading(8, true);
    btn.disabled = true;
    try {
      const data = await api("/api/shortlist", { method: "POST" });
      let msg = data.message;
      if (data.shortlisted_names?.length) {
        msg += ` — ${data.shortlisted_names.join(", ")}`;
      }
      setStatus(shortlistStatus, msg, "ok");
      render(data.candidates);
      completeStep(8);
    } catch (e) {
      setStatus(shortlistStatus, e.message, "err");
    } finally {
      btn.disabled = false;
      setLoading(8, false);
    }
  }

  async function runSendEmails() {
    const emailStatus = $("emailStatus");
    const btn = $("sendEmailsBtn");
    setLoading(9, true);
    btn.disabled = true;
    try {
      const data = await api("/api/send-test-emails", { method: "POST" });
      const s = data.summary;
      let msg = `Done — ${s.sent} sent`;
      if (s.failed) msg += `, ${s.failed} failed`;
      if (s.skipped) msg += `, ${s.skipped} skipped`;
      if (data.errors?.length) msg += `. ${data.errors[0]}`;
      setStatus(emailStatus, msg, s.failed ? "warn" : "ok");
      render(data.candidates);
      if (s.sent > 0 || s.skipped > 0) completeStep(9);
    } catch (e) {
      setStatus(emailStatus, e.message, "err");
    } finally {
      btn.disabled = false;
      setLoading(9, false);
    }
  }

  async function uploadResults(file) {
    const status = $("resultsStatus");
    const browseBtn = $("resultsBrowseBtn");
    setStatus(status, "Importing…", "");
    setLoading(10, true);
    browseBtn.disabled = true;

    try {
      const form = new FormData();
      form.append("file", file);
      const data = await api("/api/upload-results", { method: "POST", body: form });
      const s = data.summary;
      let msg = data.message;
      if (s.skipped_not_shortlisted) msg += ` (${s.skipped_not_shortlisted} non-shortlisted skipped)`;
      if (s.not_in_file?.length) msg += ` — no file match: ${s.not_in_file.slice(0, 3).join(", ")}`;
      if (data.errors?.length) msg += ` — ${data.errors[0]}`;
      setStatus(status, msg, s.not_in_file?.length || data.errors?.length ? "warn" : "ok");
      render(data.candidates);
      if (s.merged > 0) completeStep(10);
    } catch (e) {
      setStatus(status, e.message, "err");
    } finally {
      browseBtn.disabled = false;
      setLoading(10, false);
    }
  }

  async function runRescore() {
    const rescoreStatus = $("rescoreStatus");
    const btn = $("rescoreBtn");
    setLoading(11, true);
    btn.disabled = true;
    try {
      const data = await api("/api/rescore", { method: "POST" });
      let msg = data.message;
      if (data.interview_names?.length) msg += ` — ${data.interview_names.join(", ")}`;
      setStatus(rescoreStatus, msg, "ok");
      render(data.candidates);
      completeStep(11);
    } catch (e) {
      setStatus(rescoreStatus, e.message, "err");
    } finally {
      btn.disabled = false;
      setLoading(11, false);
    }
  }

  async function runSchedule() {
    const status = $("scheduleStatus");
    const btn = $("scheduleBtn");
    setLoading(13, true);
    btn.disabled = true;

    const startInput = $("scheduleStart");
    const body = {};
    if (startInput?.value) body.start_time = startInput.value;

    try {
      const data = await api("/api/schedule", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      let msg = data.message;
      const scheduled = data.log?.filter((e) => e.status === "scheduled") || [];
      if (scheduled.length) {
        const links = scheduled.map((e) => `${e.name}: ${e.meet_link || "no link"}`);
        msg += ` — ${links.join("; ")}`;
      }
      if (data.errors?.length) msg += ` — ${data.errors[0]}`;
      setStatus(status, msg, data.errors?.length ? "warn" : "ok");
      render(data.candidates);
      if (data.summary?.scheduled > 0 || data.summary?.skipped > 0) completeStep(13);
    } catch (e) {
      setStatus(status, e.message, "err");
    } finally {
      btn.disabled = false;
      setLoading(13, false);
    }
  }

  async function runSendInterviewEmails() {
    const status = $("interviewEmailStatus");
    const btn = $("sendInterviewEmailsBtn");
    setLoading(14, true);
    btn.disabled = true;
    try {
      const data = await api("/api/send-interview-emails", { method: "POST" });
      let msg = data.message;
      if (data.summary?.not_scheduled) {
        msg += " — schedule candidates in Step 13 first.";
      }
      if (data.errors?.length) msg += ` — ${data.errors[0]}`;
      setStatus(status, msg, data.errors?.length || data.summary?.not_scheduled ? "warn" : "ok");
      render(data.candidates);
      if (data.summary?.sent > 0 || data.summary?.skipped > 0) completeStep(14);
    } catch (e) {
      setStatus(status, e.message, "err");
    } finally {
      btn.disabled = false;
      setLoading(14, false);
    }
  }

  function updateGoogleUI(data) {
    const btn = $("googleAuthBtn");
    const status = $("googleAuthStatus");
    const info = $("googleConnectedInfo");
    const redirectHint = $("googleRedirectHint");
    if (!btn || !status) return;

    if (redirectHint && data?.redirect_uri) {
      redirectHint.innerHTML =
        `If Google shows <strong>redirect_uri_mismatch</strong>, add this exact URI in ` +
        `Google Cloud Console → Credentials → your OAuth client → Authorized redirect URIs:<br>` +
        `<code>${esc(data.redirect_uri)}</code> ` +
        `(also add <code>http://localhost:5000/auth/google/callback</code> if you use localhost)`;
    }

    if (data?.connected) {
      btn.textContent = "Connected";
      btn.disabled = true;
      setStatus(status, data.email ? `Signed in as ${data.email}` : "Google connected", "ok");
      if (info) {
        info.textContent = "Calendar access granted. Ready for interview scheduling.";
        info.classList.remove("hidden");
      }
      completeStep(12, false);
    } else {
      btn.textContent = "Connect Google Account";
      btn.disabled = false;
      if (info) info.classList.add("hidden");
    }
  }

  async function refreshGoogleStatus() {
    try {
      const data = await api("/api/google/status");
      updateGoogleUI(data);
      return data;
    } catch {
      return null;
    }
  }

  function init() {
    const dropZone = $("dropZone");
    const fileInput = $("fileInput");
    const browseBtn = $("browseBtn");

    document.querySelectorAll(".step-tab").forEach((btn) => {
      btn.addEventListener("click", () => {
        const step = Number(btn.dataset.step);
        if (canGoToStep(step)) goToStep(step);
      });
    });

    function pickFile() {
      fileInput.value = "";
      fileInput.click();
    }

    browseBtn.addEventListener("click", pickFile);
    dropZone.addEventListener("click", pickFile);
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

    $("saveJdBtn").addEventListener("click", saveJd);
    $("processResumesBtn").addEventListener("click", processResumes);
    $("evaluateBtn").addEventListener("click", runEvaluate);
    $("githubBtn").addEventListener("click", runGithub);
    $("academicBtn").addEventListener("click", runAcademic);
    $("scoreBtn").addEventListener("click", runScore);
    $("shortlistBtn").addEventListener("click", runShortlist);
    $("sendEmailsBtn").addEventListener("click", runSendEmails);

    const resultsDropZone = $("resultsDropZone");
    const resultsFileInput = $("resultsFileInput");
    const resultsBrowseBtn = $("resultsBrowseBtn");

    function pickResultsFile() {
      resultsFileInput.value = "";
      resultsFileInput.click();
    }

    if (resultsBrowseBtn) resultsBrowseBtn.addEventListener("click", pickResultsFile);
    if (resultsDropZone) {
      resultsDropZone.addEventListener("click", pickResultsFile);
      resultsDropZone.addEventListener("dragover", (e) => { e.preventDefault(); resultsDropZone.classList.add("over"); });
      resultsDropZone.addEventListener("dragleave", () => resultsDropZone.classList.remove("over"));
      resultsDropZone.addEventListener("drop", (e) => {
        e.preventDefault();
        resultsDropZone.classList.remove("over");
        if (e.dataTransfer.files[0]) uploadResults(e.dataTransfer.files[0]);
      });
    }
    if (resultsFileInput) {
      resultsFileInput.addEventListener("change", () => {
        if (resultsFileInput.files[0]) uploadResults(resultsFileInput.files[0]);
      });
    }

    $("rescoreBtn")?.addEventListener("click", runRescore);
    $("scheduleBtn")?.addEventListener("click", runSchedule);
    $("sendInterviewEmailsBtn")?.addEventListener("click", runSendInterviewEmails);

    $("googleAuthBtn")?.addEventListener("click", () => {
      window.location.href = "/auth/google";
    });

    const params = new URLSearchParams(window.location.search);
    if (params.get("google") === "connected") {
      goToStep(12);
      setStatus($("googleAuthStatus"), "Google connected successfully.", "ok");
      history.replaceState({}, "", "/");
    } else if (params.get("google") === "error") {
      goToStep(12);
      setStatus(
        $("googleAuthStatus"),
        "Google sign-in failed (redirect_uri_mismatch?). Add the redirect URI shown below in Google Cloud Console, save, wait 1–2 min, then retry.",
        "err"
      );
      history.replaceState({}, "", "/");
    }

    $("remarksClose")?.addEventListener("click", closeRemarksPopover);
    document.addEventListener("click", (e) => {
      const pop = $("remarksPopover");
      if (!pop || pop.classList.contains("hidden")) return;
      if (!pop.contains(e.target) && !e.target.closest(".remarks-link")) closeRemarksPopover();
    });
    $("tableBody")?.addEventListener("click", (e) => {
      const btn = e.target.closest(".remarks-link");
      if (!btn) return;
      e.stopPropagation();
      const c = cachedList[Number(btn.dataset.idx)];
      if (c) openRemarksPopover(btn, c);
    });

    $("clearBtn").addEventListener("click", async () => {
      await api("/api/candidates", { method: "DELETE" });
      render([]);
      completedSteps.clear();
      goToStep(1);
      setStatus($("uploadStatus"), "Cleared.", "ok");
    });

    updateStepNav();

    const fetchOpts = { credentials: "same-origin" };

    fetch("/api/health", fetchOpts).then((r) => r.json()).then((d) => {
      console.log("Server:", d.status);
    }).catch(() => {
      setStatus($("uploadStatus"), "Server not reachable — run: python app.py", "err");
    });

    Promise.all([
      fetch("/api/candidates", fetchOpts).then((r) => r.json()).catch(() => ({})),
      fetch("/api/jd", fetchOpts).then((r) => r.json()).catch(() => ({})),
      fetch("/api/pipeline", fetchOpts).then((r) => r.json()).catch(() => ({})),
      fetch("/api/google/status", fetchOpts).then((r) => r.json()).catch(() => ({})),
    ]).then(([candData, jdData, pipeData, googleData]) => {
      if (candData.candidates?.length) render(candData.candidates);
      if (jdData.jd) {
        $("jdInput").value = jdData.jd;
        setStatus($("jdStatus"), `Saved (${jdData.length} chars)`, "ok");
      }
      syncFromPipeline(pipeData);
      updateGoogleUI(googleData);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  window.renderCandidates = render;
})();
