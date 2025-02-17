#!/usr/bin/env just --justfile

# Print List of justfile tasks
default:
  @just --list


host := `uname -a`
# Run -> uname -a
host:
  echo {{host}}



# Clean Project
clean:
  rm -rf ./target
  rm -rf ./content/target
  rm -rf ./result
  #cargo clean
  echo 'clean complete'

# Clean downloaded tools and libs
scrub: clean
  rm -rf .cargo
  echo 'scrub complete'

# Format all files
fmt:
  nix fmt
  echo 'fmt complete'

# Install mdbook and plugins
fetch_tools:
  cargo install mdbook
  cargo install mdbook-admonish
  cargo install mdbook-footnote
  cargo install mdbook-linkcheck
  cargo install mdbook-mermaid
  cargo install mdbook-toc
  echo 'fetch_tools complete'

# Generate website by calling cargo build
build-cargo:
  cargo build

# Generate website to target/website using mdbook directly
build:
  mdbook build ./content --dest-dir ../target/website
  echo 'build complete'


