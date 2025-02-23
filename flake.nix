{
  description = "Flake for citigroup dev";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-24.11";
  };

  outputs = { self, nixpkgs }:
  let
    system = "x86_64-linux";
    pkgs = nixpkgs.legacyPackages.${system};
  in
  {
    devShells.${system}.default = pkgs.mkShell {
      # python version
      packages = with pkgs;[
        python311
      ];

      # stdc++ library for numpy
      env.LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
        pkgs.stdenv.cc.cc.lib
        pkgs.libz
      ];


      shellHook = ''
        exec zsh
        echo "Welcome to the nix shell";
        source ./env/bin/activate
      '';
    };
  };
}
