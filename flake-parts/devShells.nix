{ ... }:
{
  perSystem =
    {
      pkgs,
      config,
      self',
      inputs',
      system,
      ...
    }:
    {

      devShells.default = pkgs.mkShell {

        nativeBuildInputs = [
          self'.packages.just
          self'.packages.perl
          self'.packages.rust-oxalica
        ];

        buildInputs = [ ];

          # export CARGO_HOME="./.cargo"
          # export PATH=$PATH:''${CARGO_HOME:-~/.cargo}/bin

        shellHook = ''
          echo
          just
          echo
          echo "Welcome to the mdBook development environment!"
          echo "Run: just fetch_tools build"
        '';
      };

    };
}
