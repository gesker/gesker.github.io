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

# Install mdbook and plugins
fetch_tools:
  cargo install mdbook
  cargo install mdbook-admonish
  cargo install mdbook-footnote
  cargo install mdbook-linkcheck
  cargo install mdbook-mermaid
  cargo install mdbook-pdf
  cargo install mdbook-toc
  echo 'fetch_tools complete'

# Generate website by calling cargo build
build: clean
  mdbook build . --dest-dir ./book
  echo 'build complete'

# Generate website by calling nix build - use outside shell
build-nix:
  nix build

# # Choose NOT to have github pages build the site - manual copy
# gh-pages: build-nix
#   rm -rf ./myGithubPages
#   cp -r ./target/website ./myGithubPages
#   cp -r ./src/theme/*.css ./myGithubPages/css/
#   cp -r ./src/theme/*.js ./myGithubPages/
#   git add .
#   git commit -am "publishing site"
#   git push
