import os
import base64
from pathlib import Path
import requests
import streamlit as st

# Load SVG logo
_LOGO_PATH = Path(__file__).parent / "logo.svg"
_LOGO_B64 = base64.b64encode(_LOGO_PATH.read_bytes()).decode() if _LOGO_PATH.exists() else ""

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")
APP_ENV      = os.getenv("APP_ENV", "DEV")

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Dine – Food Nutrition Scanner",
    page_icon="🍽️",
    layout="centered",
)

# ── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700;800;900&family=Lato:wght@300;400;700;900&display=swap');

/* ---- global ---- */
body, .stApp {
    background-color: #F9F7F2;
    font-family: 'Lato', sans-serif;
    color: #2C3E50;
}

/* hide streamlit chrome */
#MainMenu, header, footer { visibility: hidden; }

/* ── HERO ── */
.hero-wrap {
    text-align: center;
    padding: 2.5rem 0 0.5rem;
}
.hero-logo {
    display: block;
    margin: 0 auto 0.3rem;
    max-width: 280px;
    animation: float 3s ease-in-out infinite;
}
@keyframes float {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-10px); }
}
.hero-sub {
    color: #5D6D7E;
    font-family: 'Lato', sans-serif;
    font-size: 1.1rem;
    font-weight: 400;
    margin-top: 0.5rem;
    margin-bottom: 2rem;
}
.hero-sub strong {
    color: #2C3E50;
}

/* ── UPLOAD AREA ── */
[data-testid="stFileUploader"] {
    border: 2px dashed #D35400;
    border-radius: 20px;
    padding: 1.4rem;
    background: rgba(211, 84, 0, 0.04);
    transition: all .25s ease;
}
[data-testid="stFileUploader"]:hover {
    border-color: #E67E22;
    background: rgba(211, 84, 0, 0.08);
    box-shadow: 0 0 30px rgba(211, 84, 0, 0.1);
}

/* ── IMAGE PREVIEW ── */
[data-testid="stImage"] {
    border-radius: 18px;
    overflow: hidden;
    box-shadow: 0 8px 32px rgba(44, 62, 80, 0.15);
    margin: 0.8rem 0;
}

/* ── ANALYSE BUTTON ── */
div.stButton > button {
    width: 100% !important;
    max-width: 100% !important;
    background: linear-gradient(135deg, #D35400 0%, #E67E22 100%);
    color: white !important;
    font-family: 'Lato', sans-serif;
    font-weight: 900;
    font-size: 1.15rem;
    letter-spacing: 0.5px;
    border: none;
    border-radius: 14px;
    padding: 0.85rem 2rem;
    margin-top: 0.6rem;
    box-shadow: 0 4px 20px rgba(211, 84, 0, 0.25);
    transition: all .25s ease;
}
div.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 30px rgba(211, 84, 0, 0.35);
    color: white !important;
}
div.stButton > button:active {
    transform: translateY(0);
}

/* ── RESULT CARD ── */
.result-card {
    background: #FFFFFF;
    border: 1px solid rgba(211, 84, 0, 0.15);
    border-radius: 22px;
    padding: 2rem 2.2rem;
    margin-top: 1.5rem;
    margin-bottom: 2rem;
    box-shadow: 0 8px 32px rgba(44, 62, 80, 0.08);
    animation: slideUp 0.5s ease-out;
}
@keyframes slideUp {
    from { opacity: 0; transform: translateY(20px); }
    to   { opacity: 1; transform: translateY(0); }
}
.dish-name {
    font-family: 'Playfair Display', serif;
    font-size: 2.4rem;
    font-weight: 800;
    letter-spacing: -0.5px;
    color: #2C3E50;
    margin-bottom: 0.4rem;
}
.confidence-badge {
    display: inline-block;
    background: rgba(39, 174, 96, 0.15);
    color: #27AE60;
    font-family: 'Lato', sans-serif;
    font-weight: 700;
    padding: 0.3rem 0.9rem;
    border-radius: 999px;
    font-size: 0.9rem;
    border: 1px solid rgba(39, 174, 96, 0.3);
    margin-bottom: 1.2rem;
}

/* ── MACRO PILLS ── */
.macros-row {
    display: flex;
    justify-content: space-between;
    gap: 0.8rem;
    margin-top: 1rem;
}
.macro-pill {
    flex: 1;
    text-align: center;
    background: #F9F7F2;
    border: 1px solid rgba(211, 84, 0, 0.12);
    border-radius: 16px;
    padding: 1.1rem 0.5rem;
    transition: all .2s ease;
}
.macro-pill:hover {
    transform: translateY(-3px);
    border-color: rgba(211, 84, 0, 0.35);
    box-shadow: 0 6px 20px rgba(211, 84, 0, 0.1);
}
.macro-icon {
    font-size: 1.4rem;
    margin-bottom: 0.25rem;
}
.macro-value {
    font-family: 'Lato', sans-serif;
    font-size: 1.7rem;
    font-weight: 900;
    line-height: 1.2;
}
.macro-label {
    color: #5D6D7E;
    font-family: 'Lato', sans-serif;
    font-size: 0.78rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-top: 0.15rem;
}

/* ── FOOTER ── */
.footer-text {
    text-align: center;
    color: #5D6D7E;
    font-family: 'Lato', sans-serif;
    font-size: 0.8rem;
    padding: 2rem 0 1rem;
}

/* ── STATUS WIDGET & STREAMLIT OVERRIDES ── */
[data-testid="stStatusWidget"] {
    border-radius: 16px;
}

/* Force light backgrounds on all Streamlit internal widgets */
[data-testid="stExpander"],
[data-testid="stAlert"],
[data-testid="stNotification"],
.stAlert, .stStatus {
    background-color: #EDE8DF !important;
    color: #2C3E50 !important;
}

/* Status container ("Analysing…" / "Done!") */
details[data-testid="stExpander"],
[data-testid="stStatusWidget"],
div[data-testid="stExpander"] {
    background-color: #EDE8DF !important;
    border: 1px solid rgba(211, 84, 0, 0.2) !important;
    border-radius: 16px !important;
    color: #2C3E50 !important;
}

details[data-testid="stExpander"] summary,
details[data-testid="stExpander"] div {
    color: #2C3E50 !important;
}

/* File uploader internal (drag-and-drop area text & background) */
[data-testid="stFileUploader"] section {
    background-color: transparent !important;
    color: #2C3E50 !important;
}
[data-testid="stFileUploader"] section > div {
    color: #5D6D7E !important;
}
[data-testid="stFileUploader"] button {
    background-color: #EDE8DF !important;
    color: #2C3E50 !important;
    border: 1px solid rgba(211, 84, 0, 0.3) !important;
}

/* Caption (model version badge) */
[data-testid="stCaptionContainer"] {
    color: #5D6D7E !important;
}

/* Warning/error messages */
[data-testid="stAlert"] {
    background-color: #EDE8DF !important;
    color: #2C3E50 !important;
    border-radius: 12px !important;
}

/* Markdown text */
p, span, label, div {
    font-family: 'Lato', sans-serif;
}

/* ── MOBILE RESPONSIVE ── */
@media (max-width: 640px) {
    .hero-wrap { padding: 1.5rem 0 0.3rem; }
    .hero-logo { max-width: 200px; }
    .hero-sub { font-size: 0.95rem; margin-bottom: 1.2rem; }

    [data-testid="stFileUploader"] {
        padding: 0.8rem;
        border-radius: 14px;
    }

    div.stButton > button {
        font-size: 1rem;
        padding: 0.75rem 1rem;
        border-radius: 12px;
    }

    .result-card {
        padding: 1.4rem 1.2rem;
        border-radius: 16px;
        margin-top: 1rem;
    }
    .dish-name { font-size: 1.6rem; }
    .confidence-badge { font-size: 0.8rem; padding: 0.2rem 0.6rem; }

    .macros-row {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 0.6rem;
    }
    .macro-pill {
        border-radius: 12px;
        padding: 0.8rem 0.4rem;
    }
    .macro-icon { font-size: 1.2rem; }
    .macro-value { font-size: 1.4rem; }
    .macro-label { font-size: 0.7rem; }
}

@media (max-width: 380px) {
    .hero-logo { max-width: 160px; }
    .dish-name { font-size: 1.3rem; }
    .macro-value { font-size: 1.2rem; }
    .macros-row { gap: 0.4rem; }
    .macro-pill { padding: 0.6rem 0.3rem; }
}
</style>
""", unsafe_allow_html=True)


# ── Hero ─────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="hero-wrap">
    <img class="hero-logo" src="data:image/svg+xml;base64,{_LOGO_B64}" alt="Dine logo"/>
    <div class="hero-sub">Snap a photo of your meal — get <strong>instant nutrition info</strong></div>
</div>
""", unsafe_allow_html=True)


# ── Upload ───────────────────────────────────────────────────────────────────
uploaded_file = st.file_uploader(
    "Drop a food photo here or tap to take one",
    type=["jpg", "jpeg", "png"],
    label_visibility="collapsed",
)

# Show image preview
if uploaded_file is not None:
    st.image(uploaded_file, width="stretch")

# ── Analyse ──────────────────────────────────────────────────────────────────
analyse_clicked = st.button("🔍  Analyse my meal")

if analyse_clicked:
    if uploaded_file is None:
        st.warning("Please upload a photo first.")
    else:
        with st.status("Analysing your meal…", expanded=True) as status:
            st.write("🖼️  Processing image…")
            files = {
                "image": (
                    uploaded_file.name,
                    uploaded_file.getvalue(),
                    uploaded_file.type,
                )
            }

            try:
                st.write("🧠  Running AI model…")
                response = requests.post(
                    f"{API_BASE_URL}/predict",
                    files=files,
                    timeout=60,
                )

                if response.status_code != 200:
                    status.update(label="Error", state="error")
                    st.error(f"Backend error: {response.text}")
                else:
                    result = response.json()
                    status.update(label="Done!", state="complete")

                    dish       = result["dish"]
                    confidence = result["confidence"]
                    nutrition  = result["nutrition"]

                    st.markdown(f"""
                    <div class="result-card">
                        <div class="dish-name">{dish.title()}</div>
                        <span class="confidence-badge">✓ {confidence:.0%} confidence</span>
                        <div class="macros-row">
                            <div class="macro-pill">
                                <div class="macro-icon">🔥</div>
                                <div class="macro-value" style="color:#D35400;">{nutrition['calories']}</div>
                                <div class="macro-label">Calories</div>
                            </div>
                            <div class="macro-pill">
                                <div class="macro-icon">💪</div>
                                <div class="macro-value" style="color:#27AE60;">{nutrition['protein_g']}g</div>
                                <div class="macro-label">Protein</div>
                            </div>
                            <div class="macro-pill">
                                <div class="macro-icon">🌾</div>
                                <div class="macro-value" style="color:#2980B9;">{nutrition['carbs_g']}g</div>
                                <div class="macro-label">Carbs</div>
                            </div>
                            <div class="macro-pill">
                                <div class="macro-icon">🥑</div>
                                <div class="macro-value" style="color:#E67E22;">{nutrition['fat_g']}g</div>
                                <div class="macro-label">Fat</div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    if APP_ENV != "PROD":
                        model_version = result.get("model_version", "unknown")
                        st.caption(f"🧪 Model: {model_version}")

            except requests.exceptions.Timeout:
                status.update(label="Timeout", state="error")
                st.error("The API took too long to respond. It may be cold-starting — try again in ~20 seconds.")
            except Exception as e:
                status.update(label="Error", state="error")
                st.error(f"Request failed: {e}")


# ── Footer ───────────────────────────────────────────────────────────────────
st.markdown(
    '<p class="footer-text">Built with ❤️ by the Dine team</p>',
    unsafe_allow_html=True,
)
