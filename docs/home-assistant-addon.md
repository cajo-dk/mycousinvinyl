# Home Assistant Add-on

This repo includes a Home Assistant add-on skeleton under `ha-addon/` that builds a single container running:

- Frontend (nginx)
- API (FastAPI)
- Workers (outbox, consumer, activity bridge, cache cleanup, pricing)
- Discogs service

## Install

1) Add this repo as a local add-on repository in Home Assistant.
2) Install the **MyCousinVinyl** add-on.
3) Configure options (see below) and start the add-on.

The default port mapping exposes the UI on port 3000 (container port 80), plus 8000/8001 for API and Discogs.

## Broker configuration

Set `message_broker` to `mqtt` to use the Mosquitto add-on. Default MQTT URL is:

```
mqtt://core-mosquitto:1883
```

If you want to keep ActiveMQ, set `message_broker` to `activemq` and provide `activemq_url`.

To add a system name prefix to MQTT topics, set `mqtt_topic_prefix` (for example: `MyCousinVinyl`).

## Required options

- `database_url`: Postgres connection string (for the Postgres 17 add-on use `core-postgres` as host).
- `azure_tenant_id`, `azure_client_id`, `azure_audience`: Azure Entra ID settings.

## Frontend runtime config

The add-on writes `/usr/share/nginx/html/env-config.js` at startup using these options:

- `vite_api_url`
- `vite_azure_client_id`
- `vite_azure_tenant_id`
- `vite_azure_redirect_uri`
- `vite_azure_group_admin`
- `vite_debug_admin`
- `vite_debug_nav`

If you leave them empty, the frontend falls back to its build-time defaults.
