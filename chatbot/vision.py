"""Injury/skin photo -> short description + suggested specialty (no diagnosis)."""
import json, sys
from chatbot.config import find_vision_models, SPECIALTIES, get_client
from src.logger import get_logger

logger = get_logger(__name__)

def analyze_image(image_b64, note=""):
    """Returns a dict, or None if no model on this Groq account can read photos."""
    prompt = ("You help a clinic front desk. Look at the photo. Reply ONLY JSON: "
              '{"description":"1-2 plain sentences of what is visible, no diagnosis","body_part":"...",'
              f'"specialty":"one of {SPECIALTIES}","urgent":true or false}}. Patient note: {note}')
    content = [{"type": "text", "text": prompt},
               {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}]
    try:
        models = find_vision_models()
    except Exception as e:
        logger.warning(f"Could not list models: {e}")
        return None
    for model in models:                      # try each candidate until one accepts the image
        try:
            r = get_client().chat.completions.create(model=model, temperature=0, max_tokens=300,
                response_format={"type": "json_object"}, messages=[{"role": "user", "content": content}])
            d = json.loads(r.choices[0].message.content)
            if d.get("specialty") not in SPECIALTIES:
                d["specialty"] = "General Physician"
            logger.info(f"Photo analysed with {model}")
            return d
        except Exception as e:
            logger.warning(f"Vision model {model} failed: {str(e)[:150]}")
    return None
