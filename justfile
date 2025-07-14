default:
  @just --list

# Update nix flake
[group('Main')]
run:
  uv run python -m src.main

[group('dev')]
stop:
  redis-cli shutdown 
