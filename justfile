# Default task: list all available commands.
default:
  @just --list

# Run the default end-to-end cycle (collect, parse, analyze).
[group('Main')]
run:
  uv run python -m src.main

# Run the end-to-end cycle using local sample logs.
[group('Main')]
sample:
  uv run python -m src.main --use-sample-logs

[group('dev')]
redis stop:
  redis-cli shutdown

[group('dev')]
test:
  uv run pytest

[group('clean')]
rmtests:
  rm tests/__pycache__/* && \
  rmdir tests/__pycache__

[group('clean')]
rmsrc:
  rm src/__pycache__/* && \
  rmdir src/__pycache__
