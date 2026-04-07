import streamlit as st
import json
import re
import ollama

# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Debug Copilot",
    page_icon="🐛",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Session State Init ────────────────────────────────────────────────────────
if "result" not in st.session_state:
    st.session_state.result = None

if "code_input" not in st.session_state:
    st.session_state.code_input = ""

if "error_input" not in st.session_state:
    st.session_state.error_input = ""

# ── Helpers ───────────────────────────────────────────────────────────────────
def analyze_code(code, error, language):
    error_context = f"\nError message:\n{error}" if error.strip() else ""

    prompt = f"""
You are a strict JSON generator.

Analyze this {language} code:

{code}

{error_context}

RULES:
- Output ONLY valid JSON
- No markdown
- No explanation outside JSON
- No extra text

Format:
{{
  "error_line": "...",
  "explanation": "...",
  "hint": "...",
  "fix": "..."
}}
"""

    try:
        response = ollama.chat(
            model="llama3",
            messages=[{"role": "user", "content": prompt}]
        )

        raw = response["message"]["content"].strip()

        # 🔍 DEBUG (you can remove later)
        st.write("RAW RESPONSE:", raw)

        # ✅ Extract JSON safely
        match = re.search(r'\{.*\}', raw, re.DOTALL)

        if match:
            json_str = match.group(0)
            try:
                return json.loads(json_str)
            except Exception:
                pass

        # ⚠️ fallback if JSON fails
        return {
            "error_line": "",
            "explanation": raw,
            "hint": "Model output not structured properly.",
            "fix": ""
        }

    except Exception as e:
        return {
            "error_line": "",
            "explanation": str(e),
            "hint": "Check if Ollama is running (ollama run llama3).",
            "fix": ""
        }

# ── UI ────────────────────────────────────────────────────────────────────────
st.title("🧑🏻‍💻 AI Debug Copilot")

col1, col2 = st.columns([2, 1])

with col1:
    code_input = st.text_area(
        "Paste your code",
        height=300,
        key="code_input"
    )

with col2:
    language = st.selectbox(
        "Language",
        ["Python", "JavaScript", "Java", "C++", "C", "Other"]
    )

    error_input = st.text_area(
        "Error (optional)",
        key="error_input"
    )

    analyze_btn = st.button("Analyze")

# ── Analyze ───────────────────────────────────────────────────────────────────
if analyze_btn:
    if not code_input.strip():
        st.warning("⚠️ Paste code first.")
    else:
        result = analyze_code(code_input, error_input, language)

        # ✅ ALWAYS store result (important fix)
        st.session_state.result = result

# ── Results ───────────────────────────────────────────────────────────────────
if st.session_state.result:
    r = st.session_state.result

    st.subheader("🔴 Error Line")
    st.code(r.get("error_line", "Not found"))

    st.subheader("💡 Explanation")
    st.write(r.get("explanation", "Not available"))

    st.subheader("🧭 Hint")
    st.write(r.get("hint", "Not available"))

    with st.expander("✅ Show Fix"):
        st.code(r.get("fix", "No fix provided"))

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("AI Debug Copilot (Ollama)")
