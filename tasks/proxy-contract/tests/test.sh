#!/bin/bash
set -euo pipefail
chown -R 0:0 /tests
chmod 700 /tests
mkdir -p /logs/verifier
chmod 700 /logs/verifier
chown 0:0 /app/nginx.conf
chmod 644 /app/nginx.conf
python3 /tests/grade.py
