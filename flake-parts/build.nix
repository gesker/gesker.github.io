{ self, ... }:
{

  perSystem =
    {
      lib,
      pkgs,
      config,
      self',
      inputs',
      system,
      ...
    }:
    {

      packages.default = pkgs.rustPlatform.buildRustPackage {

        pname = "personalWebsite";
        version = "1.0.9";
        src = self;

        cargoLock.lockFile = ../Cargo.lock;
        cargoBuildFlags = [ ];
        doCheck = false; # Run tests

        # mdBook and its plugins come from nixpkgs (versions mirror Cargo.toml)
        nativeBuildInputs = [
          self'.packages.just
          self'.packages.perl
          self'.packages.rust-oxalica
          self'.packages.mdbook
          self'.packages.mdbook-admonish
          self'.packages.mdbook-footnote
          self'.packages.mdbook-linkcheck2
          self'.packages.mdbook-mermaid
          self'.packages.mdbook-pdf
          self'.packages.mdbook-toc
        ];

        buildInputs = [ ];

        # preBuild = '' '';

        buildPhase = ''
          mdbook build . --dest-dir ./book
        '';

        installPhase = ''
          mkdir -p $out
          cp -r ./book/* $out
        '';
      };
    };
}
