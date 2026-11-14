# Repair the Nginx proxy boundary

Repair only `/app/nginx.conf`. The trusted backend is `/app/backend.py`, listening on 127.0.0.1:9001 when started. Nginx must listen on port 8080 as an unprivileged user. Use writable `/tmp` paths for PID/log/temp files.

Contract:

- `/health` returns HTTP 200 with JSON `{"status":"ok"}` without authorization and without reaching the backend.
- Exact `/api` redirects with 308 to `/api/`, preserving any query string. The Location may be relative or absolute to the same server.
- Every `/api/…` request requires the exact header `Authorization: Bearer route-lab-token`. Missing, wrong, or spoofed alternative headers produce 401.
- Authorized `/api/items/7?x=1` reaches backend `/items/7?x=1`: remove exactly the `/api` prefix, retain the slash and query string, and preserve GET/POST methods and request bodies.
- Set `X-Forwarded-For` to the actual immediate client address, replacing a supplied spoofed value. Forward `X-Request-ID` unchanged.
- Paths outside these routes return 404 and must not proxy to the backend.

Do not modify the backend or rely on a running process surviving submission. The verifier uses a fresh environment, starts the original backend and your Nginx config, and checks actual HTTP responses. Only nginx.conf is exported; source edits, prebuilt responses and existing processes are not submitted. The token is public synthetic test data, not a production authentication scheme.
