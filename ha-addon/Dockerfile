ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base:latest

FROM node:20-alpine AS frontend-build
WORKDIR /app
COPY frontend/package*.json ./frontend/
RUN cd frontend && npm ci
COPY frontend ./frontend
ARG VITE_API_URL=""
ARG VITE_AZURE_CLIENT_ID=""
ARG VITE_AZURE_TENANT_ID=""
ARG VITE_AZURE_REDIRECT_URI=""
ARG VITE_AZURE_GROUP_ADMIN=""
ARG VITE_DEBUG_ADMIN="false"
ARG VITE_DEBUG_NAV="false"
ENV VITE_API_URL=${VITE_API_URL}
ENV VITE_AZURE_CLIENT_ID=${VITE_AZURE_CLIENT_ID}
ENV VITE_AZURE_TENANT_ID=${VITE_AZURE_TENANT_ID}
ENV VITE_AZURE_REDIRECT_URI=${VITE_AZURE_REDIRECT_URI}
ENV VITE_AZURE_GROUP_ADMIN=${VITE_AZURE_GROUP_ADMIN}
ENV VITE_DEBUG_ADMIN=${VITE_DEBUG_ADMIN}
ENV VITE_DEBUG_NAV=${VITE_DEBUG_NAV}
RUN cd frontend && npm run build

FROM ${BUILD_FROM}
ENV PYTHONUNBUFFERED=1
WORKDIR /opt/mycousinvinyl

RUN apk add --no-cache \
    bash \
    gcc \
    libffi-dev \
    musl-dev \
    nginx \
    openssl-dev \
    postgresql-client \
    python3 \
    python3-dev \
    py3-pip \
    py3-setuptools \
    py3-wheel \
    supervisor

COPY backend/requirements.txt /tmp/backend-requirements.txt
COPY discogs-service/requirements.txt /tmp/discogs-requirements.txt
RUN python3 -m pip install --no-cache-dir -r /tmp/backend-requirements.txt -r /tmp/discogs-requirements.txt

COPY backend /opt/mycousinvinyl/backend
COPY discogs-service /opt/mycousinvinyl/discogs-service

COPY --from=frontend-build /app/frontend/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY supervisord.conf /etc/supervisord.conf
COPY run.sh /usr/local/bin/run.sh
COPY ha-options.py /usr/local/bin/ha-options.py
RUN cat <<'PY' > /usr/local/bin/write-env-config.py
import json
import os
from pathlib import Path


ENV_KEYS = {
    "VITE_API_URL": "VITE_API_URL",
    "VITE_AZURE_CLIENT_ID": "VITE_AZURE_CLIENT_ID",
    "VITE_AZURE_TENANT_ID": "VITE_AZURE_TENANT_ID",
    "VITE_AZURE_REDIRECT_URI": "VITE_AZURE_REDIRECT_URI",
    "VITE_AZURE_GROUP_ADMIN": "VITE_AZURE_GROUP_ADMIN",
    "VITE_DEBUG_ADMIN": "VITE_DEBUG_ADMIN",
    "VITE_DEBUG_NAV": "VITE_DEBUG_NAV",
}


def main() -> None:
    payload = {}
    for key in ENV_KEYS.values():
        payload[key] = os.getenv(key, "")

    target = Path("/usr/share/nginx/html/env-config.js")
    target.write_text("window.__ENV = " + json.dumps(payload) + ";\n")


if __name__ == "__main__":
    main()
PY

RUN chmod +x /usr/local/bin/run.sh

EXPOSE 80 8000 8001
ENTRYPOINT ["/usr/local/bin/run.sh"]
