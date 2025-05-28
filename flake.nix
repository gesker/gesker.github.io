{
  description = "mdBook Project with Custom Rust Overlay";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-parts.url = "github:hercules-ci/flake-parts";
    treefmt-nix.url = "github:numtide/treefmt-nix";
    # Rust Overlay - not a flake parts module
    rust-overlay.url = "github:oxalica/rust-overlay";

  };

  outputs =
    inputs@{
      self,
      nixpkgs,
      flake-parts,
      rust-overlay,
      ...
    }:

    flake-parts.lib.mkFlake
      {
        inherit inputs;
      }
      {

        imports = [
          # Setup Formatting
          inputs.treefmt-nix.flakeModule
          ./flake-parts/formatter.nix

          # Setup Required Packages to build packages.default
          ./flake-parts/packages-rust-oxalica.nix # Updated Rust Packages
          ./flake-parts/packages.nix # From nixpkgs

          # Actual Work on Code Here
          ./flake-parts/apps.nix # tasks ==> nix run
          ./flake-parts/devShells.nix # devShells ==> nix develop

          # The actual package we wish to build (derivation)
          ./flake-parts/build.nix
          # (import ./flake-parts/package-rust.nix {
          #   # package ==> nix build
          #   self = self;
          #   nix_package_name = nix_package_name;
          #   website_folder_name = website_folder_name;
          # })
        ];

        systems = [
          "x86_64-linux"
          "aarch64-linux"
          "x86_64-darwin"
          "aarch64-darwin"
        ];

        flake = { };

        perSystem =
          {
            config,
            self',
            inputs',
            pkgs,
            system,
            ...
          }:
          {
            # Only Debug Here
            # See flake-parts/package-rust.nix where the derivation is defined (rustPlatform.buildRustPackage instead of mkDerivation)
            # See flake-parts/devShells for the dev environment

            debug = true;

          };
      };
}
