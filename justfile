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
  rm -rf ./book
  rm -rf ./result
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
build: clean
  mdbook build . --dest-dir ./book
  @echo 'build complete'

# Generate website by calling nix build - use outside shell
build-nix:
  nix build

# Choose NOT to have github pages build the site - manual copy
publish:
  rm -rf ./book
  nix build
  nix fmt
  git add .
  git commit -am "publishing site"
  git push
  @echo 'publish complete'
