# traffic-engineering-projects
## Controller interface tests

Every push runs `tests/test_controllers.py` on GitHub Actions, one job per controller you
implement. Run them locally with `PYTHONPATH=. pytest tests` (or `-k bang_bang`, `-k p_pd_pid`,
`-k nmpc`, `-k empc` for a single controller).
