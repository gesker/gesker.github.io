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
        version = "0.0.1";
        src = self;

        cargoLock.lockFile = ../Cargo.lock;
        cargoBuildFlags = [ ];
        doCheck = false; # Run tests

        nativeBuildInputs = [
          self'.packages.google-chrome
          self'.packages.just
          self'.packages.perl
          self'.packages.rust-oxalica
        ];

        buildInputs = [ ];

        configurePhase = ''
          export CARGO_HOME="./.cargo"
          export PATH=$PATH:''${CARGO_HOME:-~/.cargo}/bin
          export CARGO_TARGET_DIR="./target"
          just fetch_tools
        '';

        # preBuild = '' '';

        buildPhase = ''
          just build
        '';

        installPhase = ''
          mkdir -p $out
          cp -r ./src/book $out
        '';
      };
    };
}
