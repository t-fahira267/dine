import os
import requests
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "").rstrip("/")

st.title("Dine")

st.write("Upload a food photo and enter portion size.")

# 1️⃣ 拍摄照片
uploaded_file = st.file_uploader(
    "Take or upload a photo",
    type=["jpg", "jpeg", "png"]
)

# 2️⃣ 输入分量
portion = st.number_input(
    "Enter portion (g)",
    min_value=1,
    value=100,
    step=10
)

# 3️⃣ 分析按钮
if st.button("Analyze"):

    if uploaded_file is None:
        st.error("Please upload a photo.")
    else:
        with st.spinner("Analyzing..."):

            # 构造 form-data
            files = {
                "image": (
                    uploaded_file.name,
                    uploaded_file.getvalue(),
                    uploaded_file.type,
                )
            }

            data = {
                "portion": portion
            }

            try:
                response = requests.post(
                    f"{API_BASE_URL}/predict",
                    files=files,
                    data=data
                )

                if response.status_code != 200:
                    st.error("Backend error.")
                else:
                    result = response.json()

                    # 4️⃣ 显示结果
                    st.success(f"Detected food: {result['dish']}")
                    st.write(f"Nutrition for {result['portion']} g")

                    nutrition = result["nutrition"]

                    st.write("### Nutrition")
                    st.write(f"Calories: {nutrition['calories']} kcal")
                    st.write(f"Protein: {nutrition['protein_g']} g")
                    st.write(f"Fat: {nutrition['fat_g']} g")
                    st.write(f"Carbs: {nutrition['carbs_g']} g")

            except Exception as e:
                st.error(f"Request failed: {e}")
