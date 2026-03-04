import os
import base64
from pathlib import Path
import requests
import streamlit as st

# Load SVG logo
_LOGO_PATH = Path(__file__).parent / "logo.svg"
_LOGO_B64 = base64.b64encode(_LOGO_PATH.read_bytes()).decode() if _LOGO_PATH.exists() else ""

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Dine – Food Nutrition Scanner",
    page_icon="🍽️",
    layout="centered",
)

# ── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap');

/* ---- global ---- */
body, .stApp {
    background: radial-gradient(ellipse at 50% 0%, #1a1040 0%, #0e1117 55%);
    font-family: 'Inter', sans-serif;
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
    color: #94a3b8;
    font-size: 1.1rem;
    font-weight: 400;
    margin-top: 0.5rem;
    margin-bottom: 2rem;
}
.hero-sub strong {
    color: #e2e8f0;
}

/* ── UPLOAD AREA ── */
[data-testid="stFileUploader"] {
    border: 2px dashed #6366f1;
    border-radius: 20px;
    padding: 1.4rem;
    background: rgba(99, 102, 241, 0.06);
    transition: all .25s ease;
}
[data-testid="stFileUploader"]:hover {
    border-color: #818cf8;
    background: rgba(99, 102, 241, 0.12);
    box-shadow: 0 0 30px rgba(99, 102, 241, 0.15);
}

/* ── IMAGE PREVIEW ── */
[data-testid="stImage"] {
    border-radius: 18px;
    overflow: hidden;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.35);
    margin: 0.8rem 0;
}

/* ── ANALYSE BUTTON ── */
div.stButton > button {
    width: 100% !important;
    max-width: 100% !important;
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 40%, #a855f7 100%);
    color: white !important;
    font-weight: 800;
    font-size: 1.15rem;
    letter-spacing: 0.5px;
    border: none;
    border-radius: 14px;
    padding: 0.85rem 2rem;
    margin-top: 0.6rem;
    box-shadow: 0 4px 20px rgba(99, 102, 241, 0.35);
    transition: all .25s ease;
}
div.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 30px rgba(139, 92, 246, 0.5);
    color: white !important;
}
div.stButton > button:active {
    transform: translateY(0);
}

/* ── RESULT CARD ── */
.result-card {
    background: linear-gradient(145deg, #1e1b4b 0%, #1e293b 50%, #172234 100%);
    border: 1px solid rgba(99, 102, 241, 0.3);
    border-radius: 22px;
    padding: 2rem 2.2rem;
    margin-top: 1.5rem;
    margin-bottom: 2rem;
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255,255,255,0.05);
    animation: slideUp 0.5s ease-out;
}
@keyframes slideUp {
    from { opacity: 0; transform: translateY(20px); }
    to   { opacity: 1; transform: translateY(0); }
}
.dish-name {
    font-size: 2.4rem;
    font-weight: 900;
    letter-spacing: -1px;
    background: linear-gradient(90deg, #f1f5f9, #e2e8f0);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.4rem;
}
.confidence-badge {
    display: inline-block;
    background: linear-gradient(90deg, rgba(34, 197, 94, 0.15), rgba(74, 222, 128, 0.1));
    color: #4ade80;
    font-weight: 700;
    padding: 0.3rem 0.9rem;
    border-radius: 999px;
    font-size: 0.9rem;
    border: 1px solid rgba(74, 222, 128, 0.2);
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
    background: rgba(15, 23, 42, 0.6);
    border: 1px solid rgba(71, 85, 105, 0.4);
    border-radius: 16px;
    padding: 1.1rem 0.5rem;
    transition: all .2s ease;
}
.macro-pill:hover {
    transform: translateY(-3px);
    border-color: rgba(99, 102, 241, 0.4);
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.2);
}
.macro-icon {
    font-size: 1.4rem;
    margin-bottom: 0.25rem;
}
.macro-value {
    font-size: 1.7rem;
    font-weight: 800;
    line-height: 1.2;
}
.macro-label {
    color: #94a3b8;
    font-size: 0.78rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-top: 0.15rem;
}

/* ── FOOTER ── */
.footer-text {
    text-align: center;
    color: #475569;
    font-size: 0.8rem;
    padding: 2rem 0 1rem;
}

/* ── STATUS WIDGET ── */
[data-testid="stStatusWidget"] {
    border-radius: 16px;
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
                                <div class="macro-value" style="color:#fb923c;">{nutrition['calories']}</div>
                                <div class="macro-label">Calories</div>
                            </div>
                            <div class="macro-pill">
                                <div class="macro-icon">💪</div>
                                <div class="macro-value" style="color:#60a5fa;">{nutrition['protein_g']}g</div>
                                <div class="macro-label">Protein</div>
                            </div>
                            <div class="macro-pill">
                                <div class="macro-icon">🌾</div>
                                <div class="macro-value" style="color:#facc15;">{nutrition['carbs_g']}g</div>
                                <div class="macro-label">Carbs</div>
                            </div>
                            <div class="macro-pill">
                                <div class="macro-icon">🥑</div>
                                <div class="macro-value" style="color:#f87171;">{nutrition['fat_g']}g</div>
                                <div class="macro-label">Fat</div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

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
