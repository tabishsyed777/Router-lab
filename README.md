# RouteLab

**Repair a real Nginx reverse proxy: prefix rewriting, authorization, query/body preservation, forwarding headers, and public health routing.**

A new terminal-task project by Tabish Syed. It contains one executable Harbor-format task, a reference repair, an independent outcome verifier, a local Docker runner, and unit/integration tests. It is a public synthetic task prototype, not an official Terminal-Bench submission or a calibrated frontier-agent benchmark.

## Run the real workload

Python 3.11+ and a local Linux Docker daemon are required. Allow several GB of free disk space for images and fresh containers. No model API key or runtime Python packages are needed for the local runner.

```sh
python -m unittest discover -s tests -p test_unit.py -v
python -m unittest discover -s tests -p test_integration.py -v
python -m routelab demo --output runs/demo
```

Open `runs/demo/report.html` alongside `report.json`. The demo grades the working reference, the unchanged broken starter, and a authorization-bypass shortcut. Success requires the reference to pass and both negative controls to fail. Commands refuse to overwrite an existing output directory; use a new `--output` to repeat.

The integration test exercises actual containers and the CLI, including generated evidence. Expected outcomes are authored from the task contract, not obtained by running the reference repair. `AGENTS.md` records the owner's requirements for tests-first development and mandatory unit and integration checks.

## Grade your own repair

```sh
python -m routelab grade --candidate path/to/nginx.conf --output runs/my-repair
```

Only that configuration file is accepted (regular nonsymlink file, maximum 64 KiB). A fresh grading container uses the original workload sources. The local runner disables container networking, limits CPU/memory/processes, keeps the verifier root-owned, and runs candidate build/server processes as an unprivileged user. No candidate code executes on the host. Exit status 0 means accepted, 1 means rejected, and 2 means input/infrastructure error. Demo status 0 means the expected positive/negative control outcomes held.

Images are built from `tasks/proxy-contract/environment` only, excluding tests and solutions. `--skip-build` reuses the current image, and `LAB_IMAGE` overrides its tag. Evidence records the resolved image ID. This is not a security guarantee against hostile candidate code, container escape, or resource-exhaustion attacks.

## Harbor 0.26.0

The task is under `tasks/proxy-contract/`, with an instruction, environment, solution, artifact declaration, and separate verifier. Harbor 0.26.0 requires Python 3.12 or newer. Install the optional pinned runner in a separate virtual environment:

```sh
python -m pip install -r requirements-harbor.txt
harbor run --path tasks/proxy-contract --agent oracle --jobs-dir runs/harbor-oracle --n-concurrent 1
harbor run --path tasks/proxy-contract --agent nop --jobs-dir runs/harbor-nop --n-concurrent 1
```

Assert the recorded outcome after each run:

```sh
python -m routelab.harbor_results runs/harbor-oracle --expected 1
python -m routelab.harbor_results runs/harbor-nop --expected 0
```

Inspect each trial's verifier reward and exception fields; a Harbor process exit code alone is not proof of a successful trial. The reference should receive 1 and NOP should receive 0 without an infrastructure error. The current task configuration validates against Harbor 0.26.0's schema version 1.4.

Harbor restores only the declared configuration artifact into a fresh environment. The default local Docker provider in this pinned release uses `network_mode = "public"`; this differs from the custom runner's enforced `--network none`. The verifier itself makes no external requests. Build-time package downloads require network access. Run trials sequentially on small machines to limit disk use.

The format follows [Harbor task structure](https://docs.harborframework.com/tasks/overview) and [separate-verifier artifact transfer](https://docs.harborframework.com/tasks/separate-verifier). Task-format compatibility and reference/NOP results do not establish official benchmark acceptance, meaningful difficulty, or model performance.

## Scope and next steps

The task is deterministic apart from temporary paths and request nonces. It has one incident design and a bounded set of outcome checks. Reference repairs and tests are public; these are not secret holdouts or an anti-cheating guarantee. No frontier agent was run and no task was submitted to Terminal-Bench or Harbor Hub. Next steps are independent task review, more failure compositions, and explicitly authorized agent difficulty calibration.

See the task's `instruction.md` for the complete behavioral contract. Generated `runs/` files stay out of Git. CI runs unit and real-container integration tests, actual Harbor oracle/NOP trials, and uploads evidence. See [validation record](docs/VALIDATION.md).

## License

MIT License. Created by Tabish Syed with AI assistance for implementation, testing, and documentation.
