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
# Preview without touching the committed build: `book/` is the published tree and
# a bare `mdbook serve` rebuilds it from src, deleting the generated resume PDFs,
# resume.txt/json, llms.txt and every injected metadata tag mid-session.
serve:
  mdbook serve --dest-dir book-draft -o

clean:
  rm -rf ./book
  rm -rf ./result
  rm -rf ./target
  rm -rf ./tmp
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
  cargo add mdbook-linkcheck2
  cargo add mdbook-mermaid
  cargo add mdbook-pdf
  cargo add mdbook-toc
  @echo 'add_tools complete'


# Install mdbook and plugins
fetch_tools: add_tools
  cargo install mdbook
  cargo install mdbook-admonish
  cargo install mdbook-footnote
  cargo install mdbook-linkcheck2
  cargo install mdbook-mermaid
  cargo install mdbook-pdf
  cargo install mdbook-toc
  @echo 'fetch_tools complete'

# Verify internal links in the built book (run after nix build)
check-links:
  python3 scripts/check_links.py ./result

# Check the rendered pages for a consistent look (cards, chips, footer, titles)
check-pages:
  python3 scripts/check_pages.py --dir ./result

# Check the font progression across every page
check-type:
  python3 scripts/check_type.py --dir ./result

# Check vertical rhythm and line spacing
check-spacing:
  python3 scripts/check_spacing.py --dir ./result

# Check logo/chip consistency for every image
check-images:
  python3 scripts/check_images.py

# Regenerate every profile-photo derivative from one source image:
# just profile-photo [path]   (avatar, og card, LinkedIn photo and banner)
profile-photo path="":
  python3 scripts/profile_photo.py {{path}}

# Add canonical, Open Graph, JSON-LD, sitemap, robots and llms.txt to ./book
seo:
  python3 scripts/seo.py ./book

# Tell seo.py to fail if the metadata is missing or stale
check-seo:
  python3 scripts/seo.py ./book --check

# Every page must be reachable from the home page and carry an inbound link
check-reachable:
  python3 scripts/check_reachable.py ./book

# Publish the resume as plain text and JSON for ATS and LLM readers
resume-exports:
  python3 scripts/resume_exports.py ./book

# Build the submitted resume PDFs (full + two-page ATS), verify the text layers
resume-pdf:
  python3 scripts/resume_pdf.py ./book --profile full
  python3 scripts/resume_pdf.py ./book --profile ats

# Check the printable resume for broken page breaks: just check-print <pdf>
check-print pdf:
  python3 scripts/check_print.py {{pdf}}

# Everything that runs without a browser, or with one
check-all: check-links check-reachable check-images check-pages check-type check-spacing
  @echo 'check-all complete'


# Generate website by calling cargo build
build:
  rm -f book.toml
  ln -sf book-build.toml book.toml
  mdbook build . --dest-dir ./book
  @echo 'build complete'

# Generate website by calling cargo build
build-with-pdf:
  rm -f book.toml
  ln -sf book-with-pdf.toml book.toml
  mdbook build . --dest-dir ./book
  @echo 'build with pdf complete'
  @echo 'pdf is in ./book/pdf directory'


#
# These tasks/targets are for use outside of a nix shell
# DO NOT USE INSIDE A NIX SHELL
#

# Generate website ia 'nix build'
build-nix: clean
  git add .
  rm -f book.toml
  ln -sf book-build.toml book.toml  
  nix fmt
  nix flake prefetch
  nix build
  @echo 'build-nix complete'

# Ensure a 'book' folder exists for github/workflows
build-nix-book: build-nix
  mkdir -p ./book
  cp -r ./result/* ./book
  chmod -R u+rw book
  python3 scripts/fix_404_base.py ./book
  python3 scripts/resume_exports.py ./book
  python3 scripts/resume_pdf.py ./book --profile full
  python3 scripts/resume_pdf.py ./book --profile ats
  python3 scripts/seo.py ./book
  python3 scripts/check_links.py ./book
  python3 scripts/check_reachable.py ./book
  @echo 'build-nix-book complete'

# Choose NOT to have github pages build the site - manual copy
publish: build-nix-book
  nix fmt
  git add .
  git commit -am "publishing site {{timestamp}}"
  git push
  @echo "publish complete {{timestamp}}"
