#!/usr/bin/env just --justfile

# Useful Reference for Flutter Commands
# https://www.geeksforgeeks.org/flutter-important-cli-commands/


# Print List of justfile tasks
default:
  @just --list

# Run -> uname -a
host := `uname -a`
host:
  echo {{host}}




# Format all files
fmt:
  dprint fmt
  echo 'fmt complete'

publish:
  just fmt
  mdbook build
  git add .
  git commit -m "publish"
  git push
  echo 'publish complete'
