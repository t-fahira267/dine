FROM python:3.10.6-buster

WORKDIR /app

COPY ../requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . frontend

ENV PORT=8501
EXPOSE 8501

CMD ["sh", "-c", "streamlit run frontend/app.py --server.address 0.0.0.0 --server.port ${PORT}"]
