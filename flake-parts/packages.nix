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
      packages.poppler_utils = pkgs.poppler_utils;

      packages.nixpkgsDependencies = [

      ];
    };
}
