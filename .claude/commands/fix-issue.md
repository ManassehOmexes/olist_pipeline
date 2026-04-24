Debug a failing Airflow task or dbt model systematically.

Steps:
1. Read the error message from $ARGUMENTS
2. Identify which layer failed: Bronze / Silver (GE) / Gold (dbt) / DAG task
3. Check the relevant log file or error output
4. Identify root cause (import error, missing file, wrong path, version mismatch, credentials)
5. Apply minimal fix — do not refactor surrounding code
6. Explain WHY the fix works in one sentence

Common issues in this project:
- `ModuleNotFoundError`: package not in `_PIP_ADDITIONAL_REQUIREMENTS`
- `No such file or directory`: volume not mounted in docker-compose.yml
- `macro takes no keyword argument`: dbt test syntax — remove `arguments:` wrapper
- `Path does not exist`: missing `--profiles-dir` in dbt command
- `REDSHIFT_PASSWORD not set`: env var fehlt in Container oder Terminal

Argument: $ARGUMENTS
