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

## Backup configuration (FR-011)

The backup worker runs inside the add-on container and requires an external path that is mounted from the host. This add-on exposes `/share` and `/media` inside the container.

1) Attach and mount the external drive in Home Assistant OS so it appears under `/share` or `/media`.
2) Create a folder for backups (example: `/share/mycousinvinyl-backups`).
3) Set the backup options in the add-on Configuration tab:
   - `backup_schedule_days` (example: `Mon,Wed,Fri`)
   - `backup_schedule_time` (example: `02:30`)
   - `backup_external_path` (example: `/share/mycousinvinyl-backups`)
   - SharePoint settings (`backup_sharepoint_site`, `backup_sharepoint_library`, `backup_sharepoint_folder`, `backup_sharepoint_tenant_id`, `backup_sharepoint_client_id`, `backup_sharepoint_client_secret`)
     - `backup_sharepoint_site` can be `https://contoso.sharepoint.com/sites/MySite` or `contoso.sharepoint.com:/sites/MySite`.

If the backup path is missing or not writable, the worker logs a failure and does not attempt the upload.
