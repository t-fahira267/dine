FROM python:3.10.6-buster
WORKDIR /app

COPY api/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY api api
COPY docs/nutrition.xlsx docs/nutrition.xlsx

ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "uvicorn api.fast:app --host 0.0.0.0 --port ${PORT}"]
