from flask import Flask, render_template, request, jsonify
import anthropic
import requests
import time
from pydantic import BaseModel, Field
from typing import List
import os

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

        storyboard = Storyboard.model_validate(tool_block.input)
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


@app.route("/generate-image", methods=["POST"])
def generate_image():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request body"}), 400

    prompt = data.get("prompt", "").strip()
    if not prompt:
        return jsonify({"error": "prompt is required"}), 400

    freepik_key = os.environ.get("FREEPIK_API_KEY")
    if not freepik_key:
        return jsonify({"error": "FREEPIK_API_KEY environment variable is not set"}), 500

    try:
        headers = {
            "x-freepik-api-key": freepik_key,
            "Content-Type": "application/json",
        }
        full_prompt = (
            "rough pencil storyboard sketch, hand-drawn animation frame, "
            "charcoal lines, minimal shading, monochrome, "
            "cinematic framing, expressive gestures, "
            "sketch construction lines visible, "
            "soft grey watercolor wash background — "
            + prompt
        )
        payload = {
            "prompt": full_prompt,
            "aspect_ratio": "widescreen_16_9",
            "resolution": "1k",
            "model": "fluid",
        }
        post_resp = requests.post(
            "https://api.freepik.com/v1/ai/mystic",
            json=payload,
            headers=headers,
            timeout=30,
        )
        post_resp.raise_for_status()
        task_id = post_resp.json()["data"]["task_id"]

        # Poll until complete (max 60 seconds)
        for _ in range(30):
            time.sleep(2)
            poll_resp = requests.get(
                f"https://api.freepik.com/v1/ai/mystic/{task_id}",
                headers=headers,
                timeout=15,
            )
            poll_resp.raise_for_status()
            result = poll_resp.json()["data"]
            if result["status"] == "COMPLETED":
                return jsonify({"image_url": result["generated"][0]})
            if result["status"] == "FAILED":
                return jsonify({"error": "Freepik image generation failed"}), 500

        return jsonify({"error": "Image generation timed out"}), 504
    except Exception as e:
        return jsonify({"error": f"Image generation failed: {str(e)}"}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
