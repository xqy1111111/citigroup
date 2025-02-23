# if you are not using nix, don't bother with this file
# if you are using nix
# run nix develop
# or using nix-direnv to use this file
# notice: you need to exec pip install -r requirements yourself
# notice: this file is only for backend develop environment
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
        echo "Welcome to the nix shell"
        python --version
        VENV_DIR=.env
        if [ ! -d "$VENV_DIR" ]; then
           python -m venv $VENV_DIR
        fi
        source ./env/bin/activate
        exec zsh
      '';
    };
  };
}
