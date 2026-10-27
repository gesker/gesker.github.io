{ ... }:
{

  perSystem =
    {
      pkgs,
      config,
      inputs',
      self',
      system,
      ...
    }:
    {
      packages.just = pkgs.just;
      packages.perl = pkgs.perl;
      packages.poppler-utils = pkgs.poppler-utils;
      packages.pdftk = pkgs.pdftk;
      packages.pandoc = pkgs.pandoc;

      # mdBook and its plugins -- versions mirror Cargo.toml
      packages.mdbook = pkgs.mdbook;
      packages.mdbook-admonish = pkgs.mdbook-admonish;
      packages.mdbook-footnote = pkgs.mdbook-footnote;
      packages.mdbook-linkcheck2 = pkgs.mdbook-linkcheck2;
      packages.mdbook-mermaid = pkgs.mdbook-mermaid;
      packages.mdbook-pdf = pkgs.mdbook-pdf;
      packages.mdbook-toc = pkgs.mdbook-toc;

      packages.nixpkgsDependencies = [

      ];
    };
}
