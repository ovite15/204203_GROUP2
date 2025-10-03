import os
import re
import time
import json
import streamlit as st

from litellm import completion

# Optional .env for local dev only
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

st.set_page_config(page_title="🥠 AI Fortune Cookie – Groq Model Comparison", page_icon="🥠", layout="wide")
st.title("🥠 AI Fortune Cookie – Groq LLM Sampler (LiteLLM)")

st.write(
    "Same prompt → 4 Groq models, side-by-side. "
    "If a reply is cut due to token limits, the app will auto-continue and stitch the result. "
    "A **Reasoning (summary)** block shows a short, user-safe rationale when the model produced hidden thinking. "
    "Raw chain-of-thought is not displayed; any inline `<think>…</think>` is redacted."
)

# ── UI controls ─────────────────────────────────────────────────────────────────
theme = st.text_input("Theme (optional):", "")
temperature = st.slider("Temperature", 0.0, 1.5, 0.9, 0.1)
max_tokens = st.slider("Max tokens", 16, 1024, 160, 16)
go = st.button("Crack 4 Cookies!", type="primary")

MODELS = [
    ("groq/llama-3.1-8b-instant", "Llama 3.1 8B Instant"),
    ("groq/openai/gpt-oss-20b", "OpenAI GPT-OSS 20B (Groq)"),
    ("groq/deepseek-r1-distill-llama-70b", "DeepSeek R1-Distill Llama 70B"),
    ("groq/qwen/qwen3-32b", "Qwen3 32B"),
]

def build_prompt(theme: str) -> str:
    return f"Write a one-sentence uplifting fortune about {theme}." if theme.strip() else "Write a one-sentence uplifting fortune."

# ── Thinking capture & redaction ────────────────────────────────────────────────
THINK_BLOCK_RE = re.compile(r"(?is)<think>.*?</think>")
THINK_CAPTURE_RE = re.compile(r"(?is)<think>(.*?)</think>")

def redact_think(text: str) -> str:
    """Replace any <think>...</think> block with a neutral placeholder."""
    if not text:
        return ""
    return THINK_BLOCK_RE.sub("[thinking hidden]", text)

# ── Helpers ────────────────────────────────────────────────────────────────────
def safe_payload_excerpt(resp):
    """
    Create a compact, safe-to-show JSON excerpt from LiteLLM response.
    Useful when a model returns empty content or is truncated.
    """
    try:
        choice = resp.choices[0]
        out = {
            "id": getattr(resp, "id", None),
            "model": getattr(resp, "model", None),
            "created": getattr(resp, "created", None),
            "choice": {
                "index": getattr(choice, "index", None),
                "finish_reason": getattr(choice, "finish_reason", None),
                "message": {
                    "role": getattr(choice.message, "role", None),
                    "content_preview": (getattr(choice.message, "content", "") or "")[:200],
                },
            },
            "usage": getattr(resp, "usage", None),
        }
        return out
    except Exception as e:
        try:
            return json.loads(resp.json())
        except Exception:
            return {"raw_repr": repr(resp), "note": f"Could not parse cleanly: {e}"}

def call_model_once(model_name, messages, temperature, max_tokens):
    return completion(
        model=model_name,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )

def call_with_continuation(model_name: str, user_prompt: str, temperature: float, max_tokens: int, rounds: int = 3):
    """
    If finish_reason == 'length', ask the model to continue and stitch the pieces.
    Keeps assistant parts as context, then adds a 'Continue.' user message.
    Also redacts <think> blocks in the final display and captures hidden thinking for summarization.
    """
    assembled_raw = ""
    reasoning_chunks = []  # captured hidden reasoning to summarize (not displayed raw)
    total_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    last_resp = None
    has_reasoning = False

    messages = [
        {"role": "system", "content": "Answer concisely in one sentence. Do not include internal notes."},
        {"role": "user", "content": user_prompt},
    ]

    last_finish = None
    start = time.time()

    for _ in range(rounds):
        resp = call_model_once(model_name, messages, temperature, max_tokens)
        last_resp = resp

        # usage (if present & numeric)
        usage = getattr(resp, "usage", None)
        if isinstance(usage, dict):
            for k in ("prompt_tokens", "completion_tokens", "total_tokens"):
                v = usage.get(k)
                if isinstance(v, int):
                    total_usage[k] += v

        # accumulate raw content
        msg = resp.choices[0].message
        part_raw = getattr(msg, "content", "") or ""
        assembled_raw += part_raw

        # capture inline <think>…</think> for summarization (not shown raw)
        for chunk in THINK_CAPTURE_RE.findall(part_raw or ""):
            if chunk.strip():
                reasoning_chunks.append(chunk.strip())

        # capture separate reasoning field (if any)
        rc = getattr(msg, "reasoning_content", None)
        if isinstance(rc, str) and rc.strip():
            reasoning_chunks.append(rc.strip())

        # reasoning flag detection
        if "<think" in part_raw.lower() or rc:
            has_reasoning = True

        # finish reason
        last_finish = getattr(resp.choices[0], "finish_reason", None)

        # stop if not truncated
        if last_finish != "length":
            break

        # if truncated, extend context and ask to continue
        messages.append({"role": "assistant", "content": part_raw})
        messages.append({"role": "user", "content": "Continue."})

    elapsed = time.time() - start

    # Build final fields
    text_clean = redact_think(assembled_raw).strip()
    raw_redacted = redact_think(assembled_raw).strip()
    payload_excerpt = safe_payload_excerpt(last_resp) if last_resp else None
    usage_out = total_usage if total_usage["total_tokens"] else (getattr(last_resp, "usage", None) if last_resp else None)
    reasoning_text = "\n\n".join(reasoning_chunks).strip() if reasoning_chunks else ""

    return {
        "ok": True,
        "text": text_clean,
        "raw_text_redacted": raw_redacted,
        "elapsed": elapsed,
        "usage": usage_out,
        "has_reasoning": has_reasoning,
        "payload_excerpt": payload_excerpt,
        "finish_reason": last_finish,
        "rounds": 1 if last_finish != "length" else None,  # informational
        "reasoning_text": reasoning_text,  # internal; summarized only
    }

def summarize_reasoning_text(reasoning_text: str) -> str:
    """
    Summarize hidden thinking into 1–2 short, user-safe bullets.
    We intentionally avoid step-by-step reproduction.
    """
    if not reasoning_text:
        return "_(no reasoning provided by the model)_"
    try:
        resp = completion(
            model="groq/llama-3.1-8b-instant",  # fast summarizer
            messages=[
                {"role": "system", "content": "You produce concise, user-safe summaries."},
                {"role": "user", "content": (
                    "Summarize the following internal model reasoning into 3-5 short bullet points. "
                    "Do NOT reveal step-by-step chains, hidden scratchpad, or private deliberations. "
                    "Focus on a high-level rationale suitable for end users.\n\n"
                    f"--- REASONING ---\n{reasoning_text}\n--- END ---"
                )},
            ],
            temperature=0.2,
            max_tokens=120,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"_Summary unavailable: {e}_"

# ── Main run ───────────────────────────────────────────────────────────────────
if go:
    if not os.getenv("GROQ_API_KEY"):
        st.error("Missing GROQ_API_KEY. Set it in your environment or .env file.")
        st.stop()

    user_prompt = build_prompt(theme)
    st.write("**Prompt sent to all models:**")
    st.code(user_prompt)

    cols = st.columns(4, gap="large")
    results = []

    for (model_id, pretty_name), col in zip(MODELS, cols):
        with col:
            st.subheader(pretty_name)
            with st.spinner("Calling model…"):
                res = call_with_continuation(model_id, user_prompt, temperature, max_tokens)
                results.append((pretty_name, res))

            if res["ok"]:
                # Final answer
                if res["text"]:
                    st.success(res["text"])
                else:
                    st.warning("No final text returned.")

                # Meta (elapsed, usage)
                meta = f"⏱ {res['elapsed']:.2f}s"
                if res["usage"]:
                    if isinstance(res["usage"], dict):
                        in_t = res["usage"].get("prompt_tokens", "—")
                        out_t = res["usage"].get("completion_tokens", "—")
                        tot_t = res["usage"].get("total_tokens", "—")
                        meta += f" · 🧮 in:{in_t} out:{out_t} total:{tot_t}"
                if res.get("finish_reason"):
                    meta += f" · 🏁 finish:{res['finish_reason']}"
                st.caption(meta)

                # Reasoning summary block (instead of showing raw thinking)
                if res["has_reasoning"]:
                    with st.expander("🧠 Reasoning (summary)"):
                        st.markdown(summarize_reasoning_text(res.get("reasoning_text", "")))

                # Raw output block (redacted) + payload excerpt
                with st.expander("🔎 Raw output (redacted) & JSON payload"):
                    st.markdown("**Raw text (redacted):**")
                    st.code(res["raw_text_redacted"] or "—")
                    st.markdown("**Provider payload (excerpt):**")
                    st.json(res["payload_excerpt"] or {"note": "No payload."})

            else:
                st.error("Model call failed.")
                st.caption(f"⏱ {res.get('elapsed', 0):.2f}s")
                with st.expander("🔎 Details"):
                    st.write(res.get("error", "Unknown error"))

    # Optional grouped list
    with st.expander("📋 Compare final outputs as a list"):
        for name, res in results:
            if res["ok"]:
                st.markdown(f"**{name}**: {res['text'] or '—'}")
            else:
                st.markdown(f"**{name}**: _error_")

st.caption("Reasoning is summarized for teaching purposes; raw chain-of-thought is redacted.")
