default:
  @just --list

[group('Main')]
run:
  uv run python -m src.main

[group('Main')]
sample:
  uv run python -m src.main --use-sample-logs

[group('dev')]
stop:
  redis-cli shutdown 

[group('dev')]
test:
  uv run pytest
