# Python Code Style

## Pflicht in jedem Skript

```python
import logging
log = logging.getLogger(__name__)
```

Kein `print()` — immer `log.info()`, `log.error()` etc.

## Funktions-Signatur

```python
def meine_funktion(param: str, count: int = 0) -> None:
    """Einzeiliger Docstring — nur wenn WHY nicht offensichtlich."""
```

Type hints überall. Docstrings nur wenn der Grund nicht aus dem Code hervorgeht.

## Error Handling

```python
try:
    result = subprocess.run([...], capture_output=True, text=True)
    if result.returncode != 0:
        log.error(result.stderr)
        raise RuntimeError(f"Befehl fehlgeschlagen: {result.args}")
    log.info(result.stdout)
except Exception as e:
    log.error("Fehler: %s", e)
    raise
```

## Credentials

```python
# Richtig
password = os.environ['REDSHIFT_PASSWORD']

# Falsch — niemals
password = "olistPipeline305!"
```

## Subprocess

Immer `capture_output=True, text=True`. Returncode prüfen. Kein `shell=True`.
