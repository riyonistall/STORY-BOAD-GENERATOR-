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
const downloadToolbar = document.getElementById("downloadToolbar");
const downloadPdfBtn  = document.getElementById("downloadPdfBtn");
const downloadDocxBtn = document.getElementById("downloadDocxBtn");

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
  frame.appendChild(frameInner);
  card.appendChild(frame);

  /* Kick off image generation asynchronously, staggered to avoid rate limits */
  setTimeout(() => fetchShotImage(shot.sketch_prompt, shot.shot_number, frame, frameInner, cameraLabel), index * 3000);

  /* Body */
  const body = el("div", "card-body");

  body.appendChild(el("p", "card-description", shot.description));

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
  promptBox.appendChild(el("p", "prompt-text", shot.sketch_prompt));

  const copyBtn = el("button", "copy-btn", "Copy");
  copyBtn.addEventListener("click", () => copyToClipboard(copyBtn, shot.sketch_prompt));
  promptBox.appendChild(copyBtn);

  promptBlock.appendChild(promptBox);
  body.appendChild(promptBlock);

  card.appendChild(body);
  return card;
}

/* ── Image generation ─────────────────────────────────────── */
async function fetchShotImage(prompt, shotNumber, frame, frameInner, cameraLabel, attempt = 0) {
  try {
    const res = await fetch("/generate-image", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt }),
    });
    const data = await res.json();
    if (!res.ok || !data.image_url) throw new Error(data.error || "No image returned");

    const img = document.createElement("img");
    img.src = data.image_url;
    img.alt = "Storyboard sketch";
    img.className = "frame-sketch-img";
    img.onload = () => {
      imageUrls[shotNumber] = data.image_url;
      frameInner.innerHTML = "";
      frameInner.appendChild(img);
      frame.classList.add("has-image");
    };
  } catch {
    if (attempt < 2) {
      cameraLabel.textContent = "Retrying sketch…";
      setTimeout(() => fetchShotImage(prompt, shotNumber, frame, frameInner, cameraLabel, attempt + 1), 5000);
    } else {
      cameraLabel.textContent = "Sketch unavailable";
      frameInner.querySelector(".frame-camera-icon").textContent = "🎥";
    }
  }
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
  row.appendChild(el("span", "detail-val", value));
  return row;
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
