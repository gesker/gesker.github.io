# gesker.github.io

About Dennis R. Gesker

## MdBook

mdbook project to create an about page.
mdbook build to create html

A git action has been created to build and deploy the git pages

### MdBook Local Development

To watch and server on localhost port 3000 as you are editing md files:

```bash
mdbook serve --open
```

### Extra Plugins Used

- [mdbook-admonish](https://github.com/tommilligan/mdbook-admonish)
- [mdbook-footnote](https://github.com/daviddrysdale/mdbook-footnote)
- [mdbook-linkcheck](https://github.com/Michael-F-Bryan/mdbook-linkcheck)
- [mdbook-mermaid](https://github.com/badboy/mdbook-mermaid)
- [mdbook-pdf](https://github.com/HollowMan6/mdbook-pdf)
- [mdbook-toc](https://github.com/badboy/mdbook-toc)

## DNS

dennis.gesker.com is CNAME to gesker.github.io
<www.gesker.com> is a server side redirect to dennis.gesker.com

## Flake

Added [flake.nix](./flake.nix) to project so that this repository can be consumed as a [Nix](https://github.com/NixOS/nixpkgs)/[NixOS](https://nixos.org) flake module. The flake in this project make use of [flake-parts](https://flake.parts).

- `nix build` to build the project using nix package system
- `nix develop`to enter a development shell and work on the project

### [mdbook-pdf](https://github.com/HollowMan6/mdbook-pdf) Issues

The [book-with-pdf.toml](book-with-pdf.toml) configuration file does NOT yet work using `nix build` does not seem to allow network access and the [mdbook-pdf](https://github.com/HollowMan6/mdbook-pdf) does seem to need network access even though it does not actually reach out to an external network but needs IO to process the website into a pdf. I don't currently have a _clean_ workaround. Perhaps but the build into a container?

Current workaround to generate the pdf manually via `nix develop` and temporarily pointing the [book.toml]./(book.toml) symlink at the [book-with-pdf.toml](./book-with-pdf.toml) configuration that includes the mdbook-pdf directives.

### [Rust](https://www.rust-lang.org/)

The [flake.nix](./flake.nix) makes use of the [Oxalica rust-overlay](https://github.com/oxalica/rust-overlay) in order to be sure to use the most recent stable version of the rust sdk and related build tools.

### Combine PDFs

After publishing print [short](https://dennis.gesker.com/resume_short_for_pdf_only.html) and [full](https://dennis.gesker.com/resume_full_for_pdf_only.html) using a web browser -- check the margins -- then...

```bash
pdftk Resume_Single_YYYYMMDD.pdf Resume_Long_YYYYMMDD.pdf cat output Resume_Combined_YYYYMMDD.pdf
```

## Zalag Logo

Zalag Logo is a registered trademark. All right reserved.
Zalag Logo Copyright Dennis Gesker
