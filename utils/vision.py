"""Minimal helpers used by src/image_to_text.py only."""
import base64, io, json, os
from litellm import completion
from PIL import Image

def _vision_model_candidates(prefer_provider=None):
    has_oa, has_gq = bool(os.getenv("OPENAI_API_KEY")), bool(os.getenv("GROQ_API_KEY"))
    oa, gq = os.getenv("OPENAI_VISION_MODEL", "gpt-4o-mini"), os.getenv("GROQ_VISION_MODEL")
    if prefer_provider == "openai": return [oa] if has_oa else []
    if prefer_provider == "groq":   return [gq] if has_gq and gq else []
    out = []
    if has_oa: out.append(oa)
    if has_gq and gq: out.append(gq)
    return out

def _image_to_data_url(image, mime="image/png"):
    fmt = "JPEG" if mime in {"image/jpeg", "image/jpg"} else "PNG"
    b = io.BytesIO(); image.save(b, format=fmt)
    return f"data:{mime};base64,{base64.b64encode(b.getvalue()).decode()}"

def _parse_json_from_text(text):
    if not text: return None
    s = text.strip()
    if s.startswith("```"):
        s = "\n".join(s.strip("`").splitlines()[1:])
    i, j = s.find("{"), s.rfind("}")
    if i != -1 and j > i:
        try: return json.loads(s[i:j+1])
        except: pass
    try: return json.loads(s)
    except: return None

def _read_image_bytes(file_obj):
    mime = "image/png"; raw = None
    if hasattr(file_obj, "getvalue"):
        try: raw = file_obj.getvalue()
        except: raw = None
        mime = getattr(file_obj, "type", mime) or mime
    elif hasattr(file_obj, "read"):
        try: raw = file_obj.read()
        except: raw = None
    elif isinstance(file_obj, (bytes, bytearray)):
        raw = bytes(file_obj)
    return raw, mime

def _normalize_items(items):
    out = []
    for it in items or []:
        if isinstance(it, dict):
            name = str(it.get("name", "")).strip()
            if name:
                try: conf = float(it.get("confidence", 0.7))
                except: conf = 0.7
                out.append({"name": name, "confidence": max(0.0, min(1.0, conf))})
        elif isinstance(it, str) and it.strip():
            out.append({"name": it.strip(), "confidence": 0.6})
    return out

def detect_ingredients_from_image(file_obj, *, temperature=0.2, max_tokens=500, prefer_provider=None):
    raw, mime = _read_image_bytes(file_obj)
    if not raw: return {"ingredients": [], "language": "th", "notes": "No image data"}
    try: img = Image.open(io.BytesIO(raw))
    except Exception as e: return {"ingredients": [], "language": "th", "notes": f"Invalid image: {e}"}

    models = _vision_model_candidates(prefer_provider=prefer_provider)
    if not models: return {"ingredients": [], "language": "th", "notes": "No vision model configured"}

    messages = [
        {"role": "system", "content": "You extract food ingredients visible in an image. Return ONLY JSON: {ingredients: [{name, confidence}], language, notes}. All ingredient names MUST be in Thai (ภาษาไทย)."},
        {"role": "user", "content": [
            {"type": "text", "text": "Detect and list the ingredients present in this image."},
            {"type": "image_url", "image_url": {"url": _image_to_data_url(img, mime=mime)}},
        ]},
    ]

    errs = []
    for m in models:
        try:
            r = completion(model=m, messages=messages, temperature=temperature, max_tokens=max_tokens)
            txt = r.choices[0].message.content if r else ""
            parsed = _parse_json_from_text(txt or "")
            if isinstance(parsed, dict) and "ingredients" in parsed:
                return {
                    "ingredients": _normalize_items(parsed.get("ingredients")),
                    "language": parsed.get("language") or "th",
                    "notes": parsed.get("notes") or "",
                }
            errs.append("Empty or unparsable response")
        except Exception as e:
            errs.append(str(e))
    return {"ingredients": [], "language": "th", "notes": "; ".join(errs) if errs else "Unknown error"}

def format_ingredient_list(ingredients):
    return ", ".join([str(i.get("name", "")).strip() for i in (ingredients or []) if str(i.get("name", "")).strip()])
