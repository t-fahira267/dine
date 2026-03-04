import os
import requests
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")

st.title("Dine")

st.write("Upload a food photo to get dish recognition and nutrition estimates.")

# 1️⃣ Taking photos
uploaded_file = st.file_uploader(
    "Take or upload a photo",
    type=["jpg", "jpeg", "png"]
)

# 2️⃣ Analysis button
if st.button("Analyze"):

    if uploaded_file is None:
        st.error("Please upload a photo.")
    else:
        with st.spinner("Analyzing..."):

            files = {
                "image": (
                    uploaded_file.name,
                    uploaded_file.getvalue(),
                    uploaded_file.type,
                )
            }

            try:
                response = requests.post(
                    f"{API_BASE_URL}/predict",
                    files=files,
                )

                if response.status_code != 200:
                    st.error(f"Backend error: {response.text}")
                else:
                    result = response.json()

                    # 3️⃣ Display results
                    st.success(f"Detected: **{result['dish']}**  (confidence: {result['confidence']:.0%})")

                    nutrition = result["nutrition"]

                    st.write("### Nutrition")
                    st.write(f"Calories: {nutrition['calories']} kcal")
                    st.write(f"Protein: {nutrition['protein_g']} g")
                    st.write(f"Fat: {nutrition['fat_g']} g")
                    st.write(f"Carbs: {nutrition['carbs_g']} g")

            except Exception as e:
                st.error(f"Request failed: {e}")
