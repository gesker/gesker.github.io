#!/usr/bin/env just --justfile

# Print List of justfile tasks
default:
  @just --list


host := `uname -a`
# Run -> uname -a
host:
  echo {{host}}


timestamp := `date +'%Y%m%d-%H%M%S'`
# Timestamp
timestamp:
  echo {{timestamp}}


# Clean Project
clean:
  rm -rf ./book
  rm -rf ./result
  rm -rf ./target
  echo 'clean complete'

# Clean downloaded tools and libs
scrub: clean
  rm -rf .cargo
  echo 'scrub complete'

# Format all files
fmt:
  nix fmt
  echo 'fmt complete'

# Add mdbook and plugins to Cargo.toml
add_tools:
  cargo add mdbook
  cargo add mdbook-admonish
  cargo add mdbook-footnote
  cargo add mdbook-linkcheck
  cargo add mdbook-mermaid
  cargo add mdbook-toc
  @echo 'add_tools complete'


# Install mdbook and plugins
fetch_tools: add_tools
  cargo install mdbook
  cargo install mdbook-admonish
  cargo install mdbook-footnote
  cargo install mdbook-linkcheck
  cargo install mdbook-mermaid
  cargo install mdbook-toc
  @echo 'fetch_tools complete'

# Generate website by calling cargo build
build:
  mdbook build . --dest-dir ./book
  @echo 'build complete'


#
# These tasks/targets are for use outside of a nix shell
# DO NOT USE INSIDE A NIX SHELL
#

# Generate website ia 'nix build'
build-nix: clean
  git add .
  nix fmt
  nix flake prefetch
  nix build
  @echo 'build-nix complete'

# Ensure a 'book' folder exists for github/workflows
build-nix-book: build-nix
  mkdir -p ./book
  cp -r ./result/* ./book
  chmod -R u+rw book
  @echo 'build-nix-book complete'

# Choose NOT to have github pages build the site - manual copy
publish: build-nix-book
  nix fmt
  git add .
  git commit -am "publishing site {{timestamp}}"
  git push
  @echo "publish complete {{timestamp}}"
