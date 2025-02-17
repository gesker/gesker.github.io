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
      packages.google-chrome = pkgs.google-chrome; # Needed by mdbook-pdf
      packages.just = pkgs.just;
      packages.perl = pkgs.perl;

      packages.nixpkgsDependencies = [

      ];
    };
}
