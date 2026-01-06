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
