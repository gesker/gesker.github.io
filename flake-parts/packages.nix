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

      packages.nixpkgsDependencies = [

      ];
    };
}
