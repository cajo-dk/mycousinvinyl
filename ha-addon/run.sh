#!/usr/bin/env bash
set -euo pipefail

if [ -f /data/options.json ]; then
  python /usr/local/bin/ha-options.py > /tmp/ha-env.sh
  set -a
  . /tmp/ha-env.sh
  set +a
fi

python /usr/local/bin/write-env-config.py

exec /usr/bin/supervisord -c /etc/supervisord.conf
