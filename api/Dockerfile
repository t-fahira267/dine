FROM python:3.10.6-buster

WORKDIR /app

COPY api/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY api api

EXPOSE 8080

# LD_PRELOAD: sklearn's libgomp must load before TensorFlow takes all TLS slots.
# The filename contains a version hash so we resolve it dynamically at container start.
CMD ["sh", "-c", "export LD_PRELOAD=$(find /usr/local/lib/python3.10/site-packages/scikit_learn.libs/ -name 'libgomp*.so*' | head -1) && uvicorn api.fast:app --host 0.0.0.0 --port ${PORT:-8080}"]
