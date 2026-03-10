/* ── DOM refs ─────────────────────────────────────────────── */
const scriptInput     = document.getElementById("scriptInput");
const charCount       = document.getElementById("charCount");
const generateBtn     = document.getElementById("generateBtn");
const exampleBtn      = document.getElementById("exampleBtn");
const loadingSection  = document.getElementById("loadingSection");
const emptyState      = document.getElementById("emptyState");
const storyboardGrid  = document.getElementById("storyboardGrid");
const errorBanner     = document.getElementById("errorBanner");
const errorText       = document.getElementById("errorText");
const downloadToolbar     = document.getElementById("downloadToolbar");
const downloadPdfBtn      = document.getElementById("downloadPdfBtn");
const downloadDocxBtn     = document.getElementById("downloadDocxBtn");
const exportSlideVideoBtn = document.getElementById("exportSlideVideoBtn");
const scriptGenBtn        = document.getElementById("scriptGenBtn");
const scriptGenModal      = document.getElementById("scriptGenModal");
const scriptGenClose      = document.getElementById("scriptGenClose");
const scriptTopicInput    = document.getElementById("scriptTopicInput");
const topicCharCount      = document.getElementById("topicCharCount");
const doGenerateScriptBtn = document.getElementById("doGenerateScriptBtn");

/* ── State ────────────────────────────────────────────────── */
let lastStoryboard = null;   // full shots array
const imageUrls    = {};     // { shot_number: url }

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

/* ── Generate Script Modal ────────────────────────────────── */
scriptGenBtn.addEventListener("click", () => {
  scriptGenModal.hidden = false;
  scriptTopicInput.focus();
});

scriptGenClose.addEventListener("click", () => {
  scriptGenModal.hidden = true;
});

scriptGenModal.addEventListener("click", (e) => {
  if (e.target === scriptGenModal) scriptGenModal.hidden = true;
});

scriptTopicInput.addEventListener("input", () => {
  topicCharCount.textContent = `${scriptTopicInput.value.length} / 500`;
});

doGenerateScriptBtn.addEventListener("click", async () => {
  const topic = scriptTopicInput.value.trim();
  if (!topic) return;

  const originalText = doGenerateScriptBtn.innerHTML;
  doGenerateScriptBtn.disabled = true;
  doGenerateScriptBtn.innerHTML = '<span class="btn-icon">⏳</span> Generating…';

  try {
    const res = await fetch("/generate-script", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ topic }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Script generation failed");

    scriptInput.value = data.script;
    updateCharCount();
    scriptGenModal.hidden = true;
    scriptTopicInput.value = "";
    topicCharCount.textContent = "0 / 500";
    scriptInput.focus();
  } catch (err) {
    alert("Error: " + err.message);
  } finally {
    doGenerateScriptBtn.disabled = false;
    doGenerateScriptBtn.innerHTML = originalText;
  }
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
  lastStoryboard = null;
  Object.keys(imageUrls).forEach((k) => delete imageUrls[k]);

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

  exportSlideVideoBtn.disabled = true;
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
    if (card.querySelector(".prompt-editor")) return; // already open
    regenBtn.style.display = "none";

    const editor = el("div", "prompt-editor");
    const inner  = el("div", "prompt-editor-inner");

    const label = el("label", "prompt-editor-label", "Edit sketch prompt");
    const textarea = document.createElement("textarea");
    textarea.className = "prompt-editor-textarea";
    const promptTextEl = card.querySelector(".prompt-text");
    textarea.value = (promptTextEl ? promptTextEl.textContent.trim() : null) || currentPrompt;
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
    inner.appendChild(label);
    inner.appendChild(textarea);
    inner.appendChild(actions);
    editor.appendChild(inner);
    card.appendChild(editor);
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
    const submitRes = await fetch("/generate-image/submit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt }),
    });
    const submitData = await submitRes.json();
    if (!submitRes.ok || !submitData.task_id) throw new Error(submitData.error || "Submit failed");

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
      exportSlideVideoBtn.disabled = false; // enable once at least one image is ready
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

/* ── Generate Film (all frames → one video) ───────────────── */
exportSlideVideoBtn.addEventListener("click", exportFrameVideo);

async function exportFrameVideo() {
  if (!lastStoryboard) return;

  const shots = lastStoryboard
    .filter((s) => imageUrls[s.shot_number])
    .sort((a, b) => a.shot_number - b.shot_number);

  if (shots.length === 0) {
    showError("No generated images available. Wait for sketches to finish first.");
    return;
  }

  if (!window.MediaRecorder) {
    showError("Your browser does not support video recording. Try Chrome or Edge.");
    return;
  }

  const btn = exportSlideVideoBtn;
  btn.disabled = true;
  btn.textContent = "Preparing…";

  const W = 1280, H = 720, FPS = 30, SEC_PER_FRAME = 4;
  const canvas = document.createElement("canvas");
  canvas.width = W;
  canvas.height = H;
  const ctx = canvas.getContext("2d");

  const mimeType = MediaRecorder.isTypeSupported("video/webm;codecs=vp9")
    ? "video/webm;codecs=vp9"
    : "video/webm";

  const stream = canvas.captureStream(FPS);
  const recorder = new MediaRecorder(stream, { mimeType, videoBitsPerSecond: 5_000_000 });
  const chunks = [];
  recorder.ondataavailable = (e) => { if (e.data.size > 0) chunks.push(e.data); };
  recorder.onstop = () => {
    const blob = new Blob(chunks, { type: "video/webm" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "storyboard-film.webm";
    a.click();
    URL.revokeObjectURL(url);
    btn.disabled = false;
    btn.innerHTML = '<span class="dl-icon">&#127909;</span> Generate Film';
  };

  recorder.start();

  for (let i = 0; i < shots.length; i++) {
    const shot = shots[i];
    btn.textContent = `Recording ${i + 1} / ${shots.length}…`;

    const proxyUrl = `/proxy-image?url=${encodeURIComponent(imageUrls[shot.shot_number])}`;
    let img;
    try {
      img = await loadImage(proxyUrl);
    } catch {
      continue;
    }

    await new Promise((resolve) => {
      const start = performance.now();
      function draw() {
        const elapsed = performance.now() - start;

        ctx.fillStyle = "#0b0b12";
        ctx.fillRect(0, 0, W, H);

        // Image — letterbox fit in upper area
        const contentH = H - 90;
        const imgAspect = img.width / img.height;
        const areaAspect = (W - 40) / contentH;
        let dw, dh;
        if (imgAspect > areaAspect) {
          dw = W - 40; dh = dw / imgAspect;
        } else {
          dh = contentH - 10; dw = dh * imgAspect;
        }
        ctx.drawImage(img, (W - dw) / 2, 10 + (contentH - dh) / 2, dw, dh);

        // Bottom info bar
        ctx.fillStyle = "rgba(0,0,0,0.88)";
        ctx.fillRect(0, H - 90, W, 90);

        ctx.fillStyle = "#e8c547";
        ctx.font = "bold 20px 'Courier New', monospace";
        ctx.fillText(`SHOT ${shot.shot_number}`, 18, H - 58);
        ctx.font = "bold 13px sans-serif";
        ctx.fillText(shot.shot_type.toUpperCase(), 18, H - 36);
        ctx.font = "12px sans-serif";
        ctx.fillStyle = "#888";
        ctx.fillText(`${shot.camera_type}  ·  ${shot.camera_angle}`, 18, H - 16);

        // Description — 2 wrapped lines
        ctx.fillStyle = "#cccccc";
        ctx.font = "13px sans-serif";
        const descX = 200, descMaxW = W - descX - 20;
        const words = shot.description.split(" ");
        let l1 = "", l2 = "";
        for (const w of words) {
          const test = l1 ? l1 + " " + w : w;
          if (ctx.measureText(test).width <= descMaxW) { l1 = test; }
          else { l2 += (l2 ? " " : "") + w; }
        }
        if (l2.length > 80) l2 = l2.slice(0, 77) + "…";
        ctx.fillText(l1, descX, H - 52);
        if (l2) ctx.fillText(l2, descX, H - 32);

        if (elapsed < SEC_PER_FRAME * 1000) {
          requestAnimationFrame(draw);
        } else {
          resolve();
        }
      }
      requestAnimationFrame(draw);
    });
  }

  recorder.stop();
}

function loadImage(src) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.crossOrigin = "anonymous";
    img.onload = () => resolve(img);
    img.onerror = reject;
    img.src = src;
  });
}

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
    setTimeout(() => { btn.textContent = "Copy"; btn.classList.remove("copied"); }, 2000);
  } catch {
    const ta = document.createElement("textarea");
    ta.value = text;
    ta.style.cssText = "position:fixed;opacity:0";
    document.body.appendChild(ta);
    ta.select();
    document.execCommand("copy");
    document.body.removeChild(ta);
    btn.textContent = "✓ Copied";
    btn.classList.add("copied");
    setTimeout(() => { btn.textContent = "Copy"; btn.classList.remove("copied"); }, 2000);
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
