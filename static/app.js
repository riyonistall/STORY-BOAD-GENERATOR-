/* ── DOM refs ─────────────────────────────────────────────── */
const scriptInput    = document.getElementById("scriptInput");
const charCount      = document.getElementById("charCount");
const generateBtn    = document.getElementById("generateBtn");
const exampleBtn     = document.getElementById("exampleBtn");
const loadingSection = document.getElementById("loadingSection");
const emptyState     = document.getElementById("emptyState");
const storyboardGrid = document.getElementById("storyboardGrid");
const errorBanner    = document.getElementById("errorBanner");
const errorText      = document.getElementById("errorText");
const downloadToolbar    = document.getElementById("downloadToolbar");
const downloadPdfBtn     = document.getElementById("downloadPdfBtn");
const downloadDocxBtn    = document.getElementById("downloadDocxBtn");
const generateVideoBtn   = document.getElementById("generateVideoBtn");
const videoSection       = document.getElementById("videoSection");
const videoGrid          = document.getElementById("videoGrid");
const playAllBtn         = document.getElementById("playAllBtn");
const regenAllVideosBtn  = document.getElementById("regenAllVideosBtn");

/* ── State ────────────────────────────────────────────────── */
let lastStoryboard = null;   // full shots array
const imageUrls    = {};     // { shot_number: url }
const videoUrls    = {};     // { shot_number: url }
let videoCards     = [];     // ordered list of { shot, videoEl } for Play All

const MAX_CHARS = 10000;

const EXAMPLE_SCRIPT = `A young girl wakes up at dawn and rushes to the window. Outside, the city is blanketed in the first snow of winter. She gasps with delight and races downstairs still in her pyjamas.

Her grandmother is already in the kitchen making tea. The girl bursts through the door and tugs her sleeve, pointing at the window. The grandmother laughs softly and nods.

The two of them step outside together into the silent, white street. The girl tilts her head back and tries to catch snowflakes on her tongue. The grandmother watches her, smiling.

They hold hands and leave two sets of footprints across the untouched snow as the winter sun rises over the rooftops.`;

/* ── Character counter ────────────────────────────────────── */
scriptInput.addEventListener("input", updateCharCount);

function updateCharCount() {
  const len = scriptInput.value.length;
  charCount.textContent = `${len.toLocaleString()} / ${MAX_CHARS.toLocaleString()}`;
  charCount.className = "char-count";
  if (len > MAX_CHARS * 0.95) charCount.classList.add("error");
  else if (len > MAX_CHARS * 0.75) charCount.classList.add("warn");
}

/* ── Example loader ───────────────────────────────────────── */
exampleBtn.addEventListener("click", () => {
  scriptInput.value = EXAMPLE_SCRIPT;
  updateCharCount();
  scriptInput.focus();
});

/* ── Generate ─────────────────────────────────────────────── */
generateBtn.addEventListener("click", generate);
scriptInput.addEventListener("keydown", (e) => {
  if (e.ctrlKey && e.key === "Enter") generate();
});

async function generate() {
  const script = scriptInput.value.trim();
  if (!script) {
    showError("Please enter a script before generating.");
    return;
  }
  if (script.length > MAX_CHARS) {
    showError(`Script is too long. Please keep it under ${MAX_CHARS.toLocaleString()} characters.`);
    return;
  }

  /* UI: loading */
  setLoading(true);
  hideError();
  emptyState.hidden = true;
  storyboardGrid.innerHTML = "";
  downloadToolbar.hidden = true;
  videoSection.hidden = true;
  videoGrid.innerHTML = "";
  playAllBtn.hidden = true;
  regenAllVideosBtn.hidden = true;
  lastStoryboard = null;
  videoCards = [];
  Object.keys(imageUrls).forEach((k) => delete imageUrls[k]);
  Object.keys(videoUrls).forEach((k) => delete videoUrls[k]);

  try {
    const res = await fetch("/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ script }),
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Unexpected error from server.");

    renderStoryboard(data);
  } catch (err) {
    showError(err.message);
    emptyState.hidden = false;
  } finally {
    setLoading(false);
  }
}

/* ── Render storyboard ────────────────────────────────────── */
function renderStoryboard(data) {
  if (!data.shots || data.shots.length === 0) {
    showError("No shots were generated. Please try again.");
    emptyState.hidden = false;
    return;
  }

  lastStoryboard = data.shots;
  Object.keys(imageUrls).forEach((k) => delete imageUrls[k]);

  data.shots.forEach((shot, index) => {
    storyboardGrid.appendChild(createCard(shot, index));
  });

  downloadToolbar.hidden = false;
}

function createCard(shot, index = 0) {
  const card = document.createElement("div");
  card.className = "shot-card";

  /* Header */
  const header = el("div", "card-header");
  header.appendChild(el("span", "card-shot-num", `Shot ${shot.shot_number}`));
  header.appendChild(el("span", "card-shot-type", shot.shot_type));
  card.appendChild(header);

  /* Sketch frame */
  const frame = el("div", "card-frame");
  const frameInner = el("div", "card-frame-inner");
  frameInner.appendChild(el("div", "frame-camera-icon", "⏳"));
  const cameraLabel = el("div", "frame-camera-label", "Generating sketch…");
  frameInner.appendChild(cameraLabel);

  /* Track current prompt so edits persist across regen cycles */
  let currentPrompt = shot.sketch_prompt;

  /* Prompt-editor overlay (shown on regen click) */
  function showPromptEditor() {
    if (frame.querySelector(".prompt-editor")) return; // already open
    regenBtn.style.display = "none";

    const editor = el("div", "prompt-editor");

    const label = el("label", "prompt-editor-label", "Edit sketch prompt");
    const textarea = document.createElement("textarea");
    textarea.className = "prompt-editor-textarea";
    /* pick up any inline edits made to the prompt-text element */
    const promptTextEl = card.querySelector(".prompt-text");
    textarea.value = (promptTextEl ? promptTextEl.textContent.trim() : null) || currentPrompt;
    textarea.rows = 4;
    textarea.spellcheck = false;

    const actions = el("div", "prompt-editor-actions");

    const cancelBtn = el("button", "prompt-editor-cancel", "Cancel");
    cancelBtn.addEventListener("click", () => {
      editor.remove();
      regenBtn.style.display = "";
    });

    const goBtn = el("button", "prompt-editor-go", "↺ Regenerate");
    goBtn.addEventListener("click", () => {
      const newPrompt = textarea.value.trim();
      if (!newPrompt) return;
      currentPrompt = newPrompt;
      /* sync the visible prompt-text element */
      const promptTextEl = card.querySelector(".prompt-text");
      if (promptTextEl) promptTextEl.textContent = newPrompt;
      editor.remove();
      regenBtn.style.display = "";
      frameInner.innerHTML = "";
      frameInner.appendChild(el("div", "frame-camera-icon", "⏳"));
      const newLabel = el("div", "frame-camera-label", "Generating sketch…");
      frameInner.appendChild(newLabel);
      frame.classList.remove("has-image");
      fetchShotImage(currentPrompt, shot.shot_number, frame, frameInner, newLabel, 0, regenBtn);
    });

    actions.appendChild(cancelBtn);
    actions.appendChild(goBtn);
    editor.appendChild(label);
    editor.appendChild(textarea);
    editor.appendChild(actions);
    frame.appendChild(editor);
    textarea.focus();
    textarea.select();
  }

  /* Regenerate button */
  const regenBtn = el("button", "regen-btn", "↺");
  regenBtn.title = "Edit prompt & regenerate";
  regenBtn.addEventListener("click", showPromptEditor);

  frame.appendChild(frameInner);
  frame.appendChild(regenBtn);
  card.appendChild(frame);

  /* Kick off image generation asynchronously, staggered to avoid rate limits */
  setTimeout(() => fetchShotImage(shot.sketch_prompt, shot.shot_number, frame, frameInner, cameraLabel, 0, regenBtn), index * 3000);

  /* Body */
  const body = el("div", "card-body");

  const descEl = el("p", "card-description", shot.description);
  makeEditable(descEl);
  body.appendChild(descEl);

  /* Camera tags */
  const tags = el("div", "camera-tags");
  tags.appendChild(cameraTag("📹", shot.camera_type));
  tags.appendChild(cameraTag("↗", shot.camera_angle));
  body.appendChild(tags);

  /* Detail rows */
  const details = el("div", "card-details");
  details.appendChild(detailRow("Action",   shot.character_action));
  details.appendChild(detailRow("Location", shot.environment));
  body.appendChild(details);

  /* Sketch prompt */
  const promptBlock = el("div", "prompt-block");
  promptBlock.appendChild(el("div", "prompt-heading", "Sketch Generation Prompt"));

  const promptBox = el("div", "prompt-box");
  const promptTextEl = el("p", "prompt-text", shot.sketch_prompt);
  makeEditable(promptTextEl);
  promptTextEl.addEventListener("blur", () => { currentPrompt = promptTextEl.textContent.trim() || currentPrompt; });
  promptBox.appendChild(promptTextEl);

  const copyBtn = el("button", "copy-btn", "Copy");
  copyBtn.addEventListener("click", () => copyToClipboard(copyBtn, promptTextEl.textContent));
  promptBox.appendChild(copyBtn);

  promptBlock.appendChild(promptBox);
  body.appendChild(promptBlock);

  card.appendChild(body);
  return card;
}

/* ── Image generation ─────────────────────────────────────── */
async function fetchShotImage(prompt, shotNumber, frame, frameInner, cameraLabel, attempt = 0, regenBtn = null) {
  if (regenBtn) regenBtn.disabled = true;
  try {
    // Step 1: submit job — fast, returns task_id immediately
    const submitRes = await fetch("/generate-image/submit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt }),
    });
    const submitData = await submitRes.json();
    if (!submitRes.ok || !submitData.task_id) throw new Error(submitData.error || "Submit failed");

    // Step 2: poll status every 3s (each call is fast, no server-side waiting)
    const imageUrl = await pollImageStatus(submitData.task_id, cameraLabel);

    const img = document.createElement("img");
    img.src = imageUrl;
    img.alt = "Storyboard sketch";
    img.className = "frame-sketch-img";
    img.onload = () => {
      imageUrls[shotNumber] = imageUrl;
      frameInner.innerHTML = "";
      frameInner.appendChild(img);
      frame.classList.add("has-image");
      if (regenBtn) regenBtn.disabled = false;
    };
  } catch (err) {
    if (attempt < 2) {
      cameraLabel.textContent = "Retrying sketch…";
      setTimeout(() => fetchShotImage(prompt, shotNumber, frame, frameInner, cameraLabel, attempt + 1, regenBtn), 5000);
    } else {
      const icon = frameInner.querySelector(".frame-camera-icon");
      if (icon) icon.textContent = "⚠️";
      cameraLabel.textContent = err?.message || "Sketch unavailable";
      if (regenBtn) regenBtn.disabled = false;
    }
  }
}

async function pollImageStatus(taskId, cameraLabel, maxAttempts = 40) {
  for (let i = 0; i < maxAttempts; i++) {
    await new Promise((r) => setTimeout(r, 3000));
    const res = await fetch(`/generate-image/status/${taskId}`);
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Status check failed");
    if (data.status === "COMPLETED") return data.image_url;
    if (data.status === "FAILED") throw new Error("Generation failed");
    if (cameraLabel) cameraLabel.textContent = "Generating sketch…";
  }
  throw new Error("Timed out waiting for sketch");
}

/* ── Video generation ─────────────────────────────────────── */
generateVideoBtn.addEventListener("click", generateVideos);

async function generateVideos() {
  if (!lastStoryboard) return;

  const shots = lastStoryboard.filter((s) => imageUrls[s.shot_number]);
  if (shots.length === 0) {
    showError("No generated sketches available yet. Wait for the sketches to finish, then try again.");
    return;
  }

  /* Reset state */
  Object.keys(videoUrls).forEach((k) => delete videoUrls[k]);
  videoCards = [];
  videoGrid.innerHTML = "";
  videoSection.hidden = false;
  playAllBtn.hidden = true;
  regenAllVideosBtn.hidden = true;
  generateVideoBtn.disabled = true;
  generateVideoBtn.innerHTML = '<span class="btn-icon">⏳</span> Generating…';
  videoSection.scrollIntoView({ behavior: "smooth", block: "start" });

  /* Build video card placeholders in order */
  shots.forEach((shot) => {
    const { card, statusLabel } = createVideoCard(shot);
    videoGrid.appendChild(card);
    videoCards.push({ shot, card, statusLabel, videoEl: null });
  });

  /* Submit video jobs — max 3 concurrent per Freepik rate limit */
  for (let i = 0; i < videoCards.length; i++) {
    if (i > 0 && i % 3 === 0) await new Promise((r) => setTimeout(r, 2000));
    fetchShotVideo(videoCards[i]);
  }
}

function createVideoCard(shot) {
  const card = el("div", "video-card");

  /* Header */
  const header = el("div", "video-card-header");
  header.appendChild(el("span", "video-card-shot-num", `Shot ${shot.shot_number}`));
  header.appendChild(el("span", "video-card-shot-type", shot.shot_type));
  card.appendChild(header);

  /* Video frame (placeholder → actual video) */
  const frame = el("div", "video-frame");
  const placeholder = el("div", "video-placeholder");
  const shimmer = el("div", "video-shimmer");
  const statusLabel = el("div", "video-status-label", "Animating scene…");
  placeholder.appendChild(shimmer);
  placeholder.appendChild(statusLabel);
  frame.appendChild(placeholder);
  card.appendChild(frame);

  /* Body */
  const body = el("div", "video-card-body");
  body.appendChild(el("p", "video-card-desc", shot.description));

  /* Actions */
  const actions = el("div", "video-card-actions");

  const dlBtn = el("button", "video-dl-btn", "⬇ Download");
  dlBtn.disabled = true;
  dlBtn.addEventListener("click", () => {
    const url = videoUrls[shot.shot_number];
    if (!url) return;
    const a = document.createElement("a");
    a.href = url;
    a.download = `shot-${shot.shot_number}.mp4`;
    a.target = "_blank";
    a.click();
  });

  const regenBtn = el("button", "video-regen-btn", "↺ Regen");
  regenBtn.disabled = true;
  regenBtn.addEventListener("click", () => {
    const entry = videoCards.find((c) => c.shot.shot_number === shot.shot_number);
    if (!entry) return;
    regenBtn.disabled = true;
    dlBtn.disabled = true;
    /* Reset frame */
    frame.innerHTML = "";
    const ph = el("div", "video-placeholder");
    ph.appendChild(el("div", "video-shimmer"));
    const lbl = el("div", "video-status-label", "Animating scene…");
    ph.appendChild(lbl);
    frame.appendChild(ph);
    entry.statusLabel = lbl;
    entry.videoEl = null;
    delete videoUrls[shot.shot_number];
    fetchShotVideo(entry);
  });

  actions.appendChild(dlBtn);
  actions.appendChild(regenBtn);
  body.appendChild(actions);
  card.appendChild(body);

  /* Stash button refs on card for later enabling */
  card._dlBtn    = dlBtn;
  card._regenBtn = regenBtn;

  return { card, statusLabel };
}

async function fetchShotVideo(entry) {
  const { shot, card } = entry;
  const imageUrl = imageUrls[shot.shot_number];
  const prompt   = shot.description;

  entry.statusLabel.textContent = "Submitting…";

  try {
    /* Submit job */
    const submitRes = await fetch("/generate-video/submit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ image_url: imageUrl, prompt }),
    });
    const submitData = await submitRes.json();
    if (!submitRes.ok || !submitData.task_id) throw new Error(submitData.error || "Submit failed");

    entry.statusLabel.textContent = "Animating scene…";

    /* Poll status (videos take longer — poll every 6s, up to 90 attempts = ~9 min) */
    const videoUrl = await pollVideoStatus(submitData.task_id, entry.statusLabel);

    videoUrls[shot.shot_number] = videoUrl;

    /* Build video player */
    const videoEl = document.createElement("video");
    videoEl.src = videoUrl;
    videoEl.controls = true;
    videoEl.loop = false;
    videoEl.className = "video-player";
    videoEl.setAttribute("playsinline", "");
    videoEl.onended = () => playNextVideo(shot.shot_number);

    const frame = card.querySelector(".video-frame");
    frame.innerHTML = "";
    frame.appendChild(videoEl);
    entry.videoEl = videoEl;

    card._dlBtn.disabled    = false;
    card._regenBtn.disabled = false;

    /* Show Play All / Regen All when all done */
    checkAllVideosReady();
  } catch (err) {
    entry.statusLabel.textContent = err?.message || "Video generation failed";
    const shimmer = card.querySelector(".video-shimmer");
    if (shimmer) shimmer.style.display = "none";
    card._regenBtn.disabled = false;
    checkAllVideosReady();
  }
}

async function pollVideoStatus(taskId, statusLabel, maxAttempts = 90) {
  for (let i = 0; i < maxAttempts; i++) {
    await new Promise((r) => setTimeout(r, 6000));
    const res  = await fetch(`/generate-video/status/${taskId}`);
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Status check failed");
    if (data.status === "COMPLETED") return data.video_url;
    if (data.status === "FAILED")    throw new Error("Video generation failed");
    if (statusLabel) {
      const mins = Math.floor((i * 6) / 60);
      const secs = (i * 6) % 60;
      statusLabel.textContent = `Animating… ${mins}:${String(secs).padStart(2, "0")}`;
    }
  }
  throw new Error("Timed out waiting for video");
}

function checkAllVideosReady() {
  const allSettled = videoCards.every(
    (c) => c.videoEl || (c.statusLabel && !c.statusLabel.textContent.startsWith("Animat") && !c.statusLabel.textContent.startsWith("Submit"))
  );
  if (allSettled) {
    generateVideoBtn.disabled = false;
    generateVideoBtn.innerHTML = '<span class="btn-icon">&#127909;</span> Generate Video';
    const hasAny = videoCards.some((c) => c.videoEl);
    if (hasAny) {
      playAllBtn.hidden = false;
      regenAllVideosBtn.hidden = false;
    }
  }
}

function playNextVideo(currentShotNumber) {
  const idx = videoCards.findIndex((c) => c.shot.shot_number === currentShotNumber);
  if (idx === -1) return;
  for (let i = idx + 1; i < videoCards.length; i++) {
    if (videoCards[i].videoEl) {
      videoCards[i].videoEl.play();
      videoCards[i].card.scrollIntoView({ behavior: "smooth", block: "center" });
      return;
    }
  }
}

playAllBtn.addEventListener("click", () => {
  const first = videoCards.find((c) => c.videoEl);
  if (!first) return;
  /* Pause/reset all then play first */
  videoCards.forEach((c) => { if (c.videoEl) { c.videoEl.pause(); c.videoEl.currentTime = 0; } });
  first.videoEl.play();
  first.card.scrollIntoView({ behavior: "smooth", block: "center" });
});

regenAllVideosBtn.addEventListener("click", generateVideos);

/* ── Download handlers ────────────────────────────────────── */
downloadPdfBtn.addEventListener("click", () => {
  window.print();
});

downloadDocxBtn.addEventListener("click", async () => {
  if (!lastStoryboard) return;
  downloadDocxBtn.disabled = true;
  downloadDocxBtn.textContent = "Generating…";

  try {
    const res = await fetch("/download/docx", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ shots: lastStoryboard, image_urls: imageUrls }),
    });
    if (!res.ok) throw new Error("Failed to generate DOCX");

    const blob = await res.blob();
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement("a");
    a.href     = url;
    a.download = "storyboard.docx";
    a.click();
    URL.revokeObjectURL(url);
  } catch (err) {
    showError("DOCX download failed: " + err.message);
  } finally {
    downloadDocxBtn.disabled = false;
    downloadDocxBtn.innerHTML = '<span class="dl-icon">&#128196;</span> Download DOCX';
  }
});

/* ── Helpers ──────────────────────────────────────────────── */
function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function cameraTag(icon, label) {
  const tag = el("span", "camera-tag");
  tag.appendChild(el("span", "camera-tag-icon", icon));
  tag.appendChild(document.createTextNode(label));
  return tag;
}

function detailRow(key, value) {
  const row = el("div", "detail-row");
  row.appendChild(el("span", "detail-key", key));
  const valEl = el("span", "detail-val", value);
  makeEditable(valEl);
  row.appendChild(valEl);
  return row;
}

/* Makes any element click-to-edit inline */
function makeEditable(node) {
  node.classList.add("editable-field");
  node.setAttribute("title", "Click to edit");
  let original = "";

  node.addEventListener("click", () => {
    if (node.contentEditable === "true") return;
    original = node.textContent;
    node.contentEditable = "true";
    node.classList.add("editing");
    node.focus();
    const range = document.createRange();
    range.selectNodeContents(node);
    const sel = window.getSelection();
    sel.removeAllRanges();
    sel.addRange(range);
  });

  node.addEventListener("blur", () => {
    node.contentEditable = "false";
    node.classList.remove("editing");
    if (!node.textContent.trim()) node.textContent = original;
  });

  node.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); node.blur(); }
    if (e.key === "Escape") { node.textContent = original; node.blur(); }
  });
}

async function copyToClipboard(btn, text) {
  try {
    await navigator.clipboard.writeText(text);
    btn.textContent = "✓ Copied";
    btn.classList.add("copied");
    setTimeout(() => {
      btn.textContent = "Copy";
      btn.classList.remove("copied");
    }, 2000);
  } catch {
    /* Fallback for older browsers */
    const ta = document.createElement("textarea");
    ta.value = text;
    ta.style.cssText = "position:fixed;opacity:0";
    document.body.appendChild(ta);
    ta.select();
    document.execCommand("copy");
    document.body.removeChild(ta);
    btn.textContent = "✓ Copied";
    btn.classList.add("copied");
    setTimeout(() => {
      btn.textContent = "Copy";
      btn.classList.remove("copied");
    }, 2000);
  }
}

function setLoading(on) {
  loadingSection.hidden = !on;
  generateBtn.disabled  = on;
  generateBtn.innerHTML = on
    ? '<span class="btn-icon">⏳</span> Generating…'
    : '<span class="btn-icon">▶</span> Generate Storyboard';
}

function showError(msg) {
  errorText.textContent = msg;
  errorBanner.hidden = false;
  errorBanner.scrollIntoView({ behavior: "smooth", block: "center" });
}

function hideError() {
  errorBanner.hidden = true;
}
