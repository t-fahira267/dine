FROM python:3.10.6-buster

WORKDIR /app

COPY frontend/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY frontend frontend
COPY frontend/.streamlit /root/.streamlit

CMD ["sh", "-c", "streamlit run frontend/app.py --server.address 0.0.0.0 --server.port ${PORT:-8080} --server.headless true"]
