from flask import Flask, render_template, request, jsonify, send_file, Response
import anthropic
import requests
import time
import io
from concurrent.futures import ThreadPoolExecutor, as_completed
from pydantic import BaseModel, Field, ValidationError
from typing import List
import os
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

app = Flask(__name__)

SYSTEM_PROMPT = """You are a visual storyboard assistant for film and advertising production.

Your task is to convert a script into storyboard sketches. For every script provided, you must:
1. Break the script into clear shots/beats (6-12 maximum for any script length)
2. Generate a visual storyboard description for each shot
3. Output sketch prompts for generating rough storyboard frames

The sketches should resemble hand-drawn storyboard frames used in animation studios:
- rough pencil/charcoal lines
- minimal shading
- expressive characters
- imperfect sketch strokes
- soft grey or muted color washes
- simple background shapes
- cinematic framing

Visual Style Rules — All generated storyboard frames must follow this style:

Illustration Style:
- rough charcoal or pencil sketch
- loose animation storyboard style
- hand drawn imperfect strokes
- minimal detail
- soft grey watercolor background wash
- expressive character gestures
- sketch construction lines visible
- thick and thin line variation

Color Treatment:
- mostly monochrome
- light blue or grey wash for characters
- white clothing
- minimal background tone
- no bright colors

Composition:
- cinematic framing
- strong silhouettes
- focus on body language
- simple backgrounds
- perspective lines lightly sketched

Important Rules:
- Always generate shots sequentially
- Never skip beats from the script
- Keep sketch prompts clear and image-generation ready
- Focus on visual storytelling
- Use cinematic framing language
- For long scripts, break into 6-12 storyboard frames maximum
"""


class StoryboardShot(BaseModel):
    shot_number: int = Field(description="Sequential shot number starting from 1")
    shot_type: str = Field(
        description="Shot type label e.g. 'Wide establishing shot', 'Medium shot', 'Close up', 'Over the shoulder'"
    )
    description: str = Field(
        description="Clear visual description of what is seen in this shot (2-3 sentences)"
    )
    camera_type: str = Field(
        description="Camera shot size e.g. 'wide shot', 'medium shot', 'close up', 'extreme close up'"
    )
    camera_angle: str = Field(
        description="Camera angle e.g. 'eye level', 'slightly elevated', 'low angle', \"bird's eye view\", 'dutch angle'"
    )
    character_action: str = Field(
        description="What the character(s) are doing in this shot"
    )
    environment: str = Field(description="The setting or environment of the shot")
    sketch_prompt: str = Field(
        description="Detailed image-generation prompt for creating a rough storyboard sketch. Must describe the animation style, character action, environment, camera framing, and visual style cues."
    )


class Storyboard(BaseModel):
    shots: List[StoryboardShot] = Field(
        description="Ordered list of storyboard shots, maximum 12"
    )


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generate-script", methods=["POST"])
def generate_script():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request body"}), 400

    topic = data.get("topic", "").strip()
    if not topic:
        return jsonify({"error": "Topic is required"}), 400

    if len(topic) > 500:
        return jsonify({"error": "Topic is too long. Maximum 500 characters."}), 400

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return jsonify({"error": "ANTHROPIC_API_KEY environment variable is not set"}), 500

    try:
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=1500,
            system=(
                "You are a professional screenwriter specializing in short films. "
                "Write a vivid, visual prose script based on the given topic or idea. "
                "The script should be 250–600 words. Write it as flowing narrative prose — "
                "describe scenes, actions, environments, and character behaviour visually "
                "as a director would see them. Avoid heavy dialogue. Focus on what the camera sees. "
                "Output only the script text, no titles, no extra commentary."
            ),
            messages=[{"role": "user", "content": f"Write a short film script about: {topic}"}],
        )
        script = message.content[0].text.strip()
        return jsonify({"script": script})
    except Exception as e:
        return jsonify({"error": f"Script generation failed: {str(e)}"}), 500


@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request body"}), 400

    script = data.get("script", "").strip()
    if not script:
        return jsonify({"error": "Script is required"}), 400

    if len(script) > 10000:
        return jsonify({"error": "Script is too long. Maximum 10,000 characters."}), 400

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return (
            jsonify({"error": "ANTHROPIC_API_KEY environment variable is not set"}),
            500,
        )

    try:
        client = anthropic.Anthropic(api_key=api_key)

        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=[
                {
                    "name": "create_storyboard",
                    "description": "Create a structured storyboard from the script",
                    "input_schema": Storyboard.model_json_schema(),
                }
            ],
            tool_choice={"type": "tool", "name": "create_storyboard"},
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Convert this script into a detailed storyboard with shot breakdown "
                        "and sketch generation prompts for each frame:\n\n"
                        + script
                    ),
                }
            ],
        )

        tool_block = next(
            (b for b in response.content if b.type == "tool_use"), None
        )
        if not tool_block:
            return jsonify({"error": "No storyboard was generated."}), 500

        try:
            storyboard = Storyboard.model_validate(tool_block.input)
        except ValidationError:
            # Salvage any individually-valid shots (skip empty/incomplete ones)
            raw_shots = tool_block.input.get("shots", []) if isinstance(tool_block.input, dict) else []
            valid_shots = []
            for s in raw_shots:
                try:
                    valid_shots.append(StoryboardShot.model_validate(s))
                except ValidationError:
                    continue
            if not valid_shots:
                return jsonify({"error": "Storyboard generation produced no valid shots. Please try again."}), 500
            storyboard = Storyboard(shots=valid_shots)

        return jsonify(storyboard.model_dump())

    except anthropic.AuthenticationError:
        return (
            jsonify({"error": "Invalid API key. Please check your ANTHROPIC_API_KEY."}),
            401,
        )
    except anthropic.RateLimitError:
        return (
            jsonify({"error": "Rate limited. Please wait a moment and try again."}),
            429,
        )
    except anthropic.BadRequestError as e:
        return jsonify({"error": f"Invalid request: {str(e)}"}), 400
    except anthropic.APIError as e:
        return jsonify({"error": f"API error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Error generating storyboard: {str(e)}"}), 500


def _freepik_headers():
    key = os.environ.get("FREEPIK_API_KEY")
    if not key:
        return None, jsonify({"error": "FREEPIK_API_KEY environment variable is not set"}), 500
    return {"x-freepik-api-key": key, "Content-Type": "application/json"}, None, None


@app.route("/generate-image/submit", methods=["POST"])
def generate_image_submit():
    """Submit a generation job to Freepik. Returns task_id immediately."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request body"}), 400

    prompt = data.get("prompt", "").strip()
    if not prompt:
        return jsonify({"error": "prompt is required"}), 400

    headers, err_resp, err_code = _freepik_headers()
    if err_resp:
        return err_resp, err_code

    try:
        full_prompt = (
            "rough pencil storyboard sketch, hand-drawn animation frame, "
            "charcoal lines, minimal shading, monochrome, "
            "cinematic framing, expressive gestures, "
            "sketch construction lines visible, "
            "soft grey watercolor wash background — "
            + prompt
        )
        resp = requests.post(
            "https://api.freepik.com/v1/ai/mystic",
            json={"prompt": full_prompt, "aspect_ratio": "widescreen_16_9", "resolution": "1k"},
            headers=headers,
            timeout=15,
        )
        resp.raise_for_status()
        return jsonify({"task_id": resp.json()["data"]["task_id"]})
    except Exception as e:
        return jsonify({"error": f"Submit failed: {str(e)}"}), 500


@app.route("/generate-image/status/<task_id>", methods=["GET"])
def generate_image_status(task_id):
    """Check the status of a Freepik generation task. Single fast call."""
    headers, err_resp, err_code = _freepik_headers()
    if err_resp:
        return err_resp, err_code

    try:
        resp = requests.get(
            f"https://api.freepik.com/v1/ai/mystic/{task_id}",
            headers=headers,
            timeout=8,
        )
        resp.raise_for_status()
        result = resp.json()["data"]
        status = result.get("status")
        generated = result.get("generated") or []
        if status == "COMPLETED" and generated:
            return jsonify({"status": "COMPLETED", "image_url": generated[0]})
        if status == "FAILED":
            return jsonify({"status": "FAILED", "error": "Generation failed"}), 500
        return jsonify({"status": status})
    except Exception as e:
        return jsonify({"error": f"Status check failed: {str(e)}"}), 500


@app.route("/generate-video/submit", methods=["POST"])
def generate_video_submit():
    """Submit an image-to-video job to Freepik Kling v2. Returns task_id immediately."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request body"}), 400

    image_url = data.get("image_url", "").strip()
    prompt = data.get("prompt", "").strip()
    if not image_url:
        return jsonify({"error": "image_url is required"}), 400

    headers, err_resp, err_code = _freepik_headers()
    if err_resp:
        return err_resp, err_code

    try:
        payload = {"image": image_url, "duration": "5"}
        if prompt:
            payload["prompt"] = prompt[:2500]
        resp = requests.post(
            "https://api.freepik.com/v1/ai/image-to-video/kling-v2",
            json=payload,
            headers=headers,
            timeout=15,
        )
        resp.raise_for_status()
        return jsonify({"task_id": resp.json()["data"]["task_id"]})
    except Exception as e:
        return jsonify({"error": f"Video submit failed: {str(e)}"}), 500


@app.route("/generate-video/status/<task_id>", methods=["GET"])
def generate_video_status(task_id):
    """Poll the status of a Freepik image-to-video task."""
    headers, err_resp, err_code = _freepik_headers()
    if err_resp:
        return err_resp, err_code

    try:
        resp = requests.get(
            f"https://api.freepik.com/v1/ai/image-to-video/kling-v2/{task_id}",
            headers=headers,
            timeout=8,
        )
        resp.raise_for_status()
        result = resp.json()["data"]
        status = result.get("status")
        generated = result.get("generated") or []
        if status == "COMPLETED" and generated:
            return jsonify({"status": "COMPLETED", "video_url": generated[0]})
        if status == "FAILED":
            return jsonify({"status": "FAILED", "error": "Video generation failed"}), 500
        return jsonify({"status": status})
    except Exception as e:
        return jsonify({"error": f"Video status check failed: {str(e)}"}), 500


@app.route("/proxy-image")
def proxy_image():
    """Proxy Freepik image URLs so the client canvas can draw them without CORS errors."""
    from urllib.parse import urlparse
    url = request.args.get("url", "").strip()
    if not url:
        return jsonify({"error": "url is required"}), 400
    # Only allow Freepik-served image URLs for security
    parsed = urlparse(url)
    allowed = ("freepik.com", "ik.imagekit.io", "ai-generation.freepik.com")
    if not any(parsed.netloc.endswith(h) for h in allowed):
        return jsonify({"error": "URL not allowed"}), 403
    try:
        resp = requests.get(url, timeout=20, stream=False)
        resp.raise_for_status()
        content_type = resp.headers.get("Content-Type", "image/jpeg")
        return Response(
            resp.content,
            content_type=content_type,
            headers={"Access-Control-Allow-Origin": "*", "Cache-Control": "public, max-age=3600"},
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/download/docx", methods=["POST"])
def download_docx():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request body"}), 400

    shots = data.get("shots", [])
    image_urls = data.get("image_urls", {})

    # Fetch all images in parallel (max 15s total)
    def fetch_image(key_url):
        key, url = key_url
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            return key, io.BytesIO(resp.content)
        except Exception:
            return key, None

    image_data = {}
    if image_urls:
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = {executor.submit(fetch_image, (k, v)): k for k, v in image_urls.items() if v}
            for future in as_completed(futures, timeout=15):
                try:
                    key, stream = future.result()
                    if stream:
                        image_data[key] = stream
                except Exception:
                    pass

    doc = Document()

    # Title
    title = doc.add_heading("Storyboard", 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    for shot in shots:
        shot_num = str(shot.get("shot_number", ""))
        key = int(shot_num) if shot_num.isdigit() else shot_num

        # Shot heading
        doc.add_heading(f"Shot {shot_num}  —  {shot.get('shot_type', '')}", level=1)

        # Sketch image (if fetched successfully)
        img_stream = image_data.get(key)
        if img_stream:
            try:
                doc.add_picture(img_stream, width=Inches(6))
                doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
            except Exception:
                pass

        # Description
        desc = doc.add_paragraph(shot.get("description", ""))
        desc.paragraph_format.space_after = Pt(8)

        # Details table
        table = doc.add_table(rows=4, cols=2)
        table.style = "Table Grid"
        rows_data = [
            ("Camera Type",  shot.get("camera_type", "")),
            ("Camera Angle", shot.get("camera_angle", "")),
            ("Action",       shot.get("character_action", "")),
            ("Location",     shot.get("environment", "")),
        ]
        for i, (key_label, val) in enumerate(rows_data):
            table.rows[i].cells[0].text = key_label
            table.rows[i].cells[1].text = val
            table.rows[i].cells[0].paragraphs[0].runs[0].bold = True

        doc.add_paragraph()  # spacer between shots

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)

    return send_file(
        buf,
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        as_attachment=True,
        download_name="storyboard.docx",
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
