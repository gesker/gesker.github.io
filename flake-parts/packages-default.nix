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
        version = "1.0.3";
        src = self;

        cargoLock.lockFile = ../Cargo.lock;
        cargoBuildFlags = [ ];
        doCheck = false; # Run tests

        nativeBuildInputs = [
          self'.packages.just
          self'.packages.perl
          self'.packages.rust-oxalica
        ];

        buildInputs = [ ];

        configurePhase = ''
          export CARGO_HOME="./.cargo"
          export PATH=$CARGO_HOME/bin:$PATH
          just fetch_tools
        '';

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
