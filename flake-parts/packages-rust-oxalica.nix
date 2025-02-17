{ self, inputs, ... }:
{

  perSystem =
    {
      pkgs,
      config,
      inputs',
      system,
      ...
    }:
    {

      _module.args.pkgs = import self.inputs.nixpkgs {
        inherit system;
        overlays = [
          (import inputs.rust-overlay)
          (final: prev: {
            # This is where you can add custom packages or override existing ones
          })
        ];
        config.allowUnfree = true;
      };

      packages.rust-oxalica = (
        pkgs.rust-bin.stable.latest.default.override {
          extensions = [
            "cargo"
            "clippy"
            "llvm-bitcode-linker"
            "llvm-tools"
            "reproducible-artifacts"
            "rls"
            "rust-analysis"
            "rust-analyzer"
            "rust-docs"
            "rust-src"
            "rust-std"
            "rust"
            "rustc-docs"
            "rustc"
            "rustfmt"
          ];
        }
      );

    };
}
