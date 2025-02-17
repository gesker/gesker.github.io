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

      apps = {

        tool-info = {
          type = "app";
          program = "${pkgs.writeShellScriptBin "tool-info" ''
            ${pkgs.rustc}/bin/rustc --version
          ''}/bin/tool-info";
        };

        build-book = {
          type = "app";
          program = "${pkgs.writeShellScriptBin "build-book" ''
            ${pkgs.mdbook}/bin/mdbook build
          ''}/bin/build-book";
        };

        serve-book = {
          type = "app";
          program = "${pkgs.writeShellScriptBin "serve-book" ''
            ${pkgs.mdbook}/bin/mdbook serve
          ''}/bin/serve-book";
        };
      };

    };
}
