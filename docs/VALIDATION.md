# RouteLab validation

Tests-first development began with failing imports and a failing CLI integration check before the runner/verifier existed. Three verifier/runner unit tests and a real Docker integration test were then made green. A fourth unit test was written and failed before adding strict validation of Harbor's recorded reward and exception fields.

The current suite has four unit tests and one real-container integration test. The integration test accepts the reference, rejects the unchanged starter and an authorization-bypass configuration, and checks HTML evidence generation.

The reference passes 15 outcome checks: Nginx configuration, fresh servers, public health response, four authorization rejections, three unknown routes, the exact-prefix redirect/query behavior, and four dynamic GET/POST requests. Requests include fresh nonces, query strings, body payloads, request IDs, and a deliberately spoofed forwarding address. Expected responses come from the documented contract, not the reference configuration.

Actual Harbor 0.26.0 local-Docker trials with separate verification produced oracle reward 1 and NOP reward 0, both with reward_valid=true and no exception. The package validates against schema version 1.4. Initial infrastructure trials encountered workspace disk exhaustion; fresh sequential trials after clearing temporary caches produced the results above. A workspace-only wrapper relocated Harbor cache constants because the managed environment's home is read-only; task/verifier execution was not modified.

The reference initially failed because unused Nginx module temp paths still pointed into a privileged directory. Moving all temp paths into /tmp fixed the unprivileged startup; the incident starter now starts successfully and is rejected for incorrect routing/authentication behavior rather than an unrelated startup failure.

No model/terminal agent was evaluated. These public synthetic controls establish implemented behavior and solvability, not benchmark acceptance, calibrated difficulty, secrecy, or a comprehensive hostile-code sandbox. The known bearer token is synthetic fixture data. The Docker base tag and apt packages are not fully pinned; evidence records the measured local image ID.
