# Development requirements

The owner requires test-driven development for every behavior change: write and run a failing test, implement the smallest change, then refactor with tests green. Always run both unit and real container integration tests before handoff. Never change expected results merely to accept an incorrect candidate.

```sh
python -m unittest discover -s tests -p test_unit.py -v
python -m unittest discover -s tests -p test_integration.py -v
```

Integration tests need a local Docker daemon. Verify actual outcomes in a fresh container. Keep solutions and verifiers out of the agent image. Only the specified configuration artifact may cross into verification. Do not claim agent capability, difficulty calibration, or official Terminal-Bench inclusion from reference/NOP results.
