FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir starlette==0.46.2 uvicorn==0.34.0

COPY server.py ./
COPY fixtures/ ./fixtures/

ENV FAKE_SIDECAR=""
ENV LISTEN_PORT="8080"

EXPOSE 8080 9005

CMD ["sh", "-c", "uvicorn server:app --host 0.0.0.0 --port ${LISTEN_PORT}"]
