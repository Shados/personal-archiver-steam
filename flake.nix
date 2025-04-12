{
  description = "poetry2nix packaging for personal-archiver-steam";

  inputs.flake-utils.url = "github:numtide/flake-utils";
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  inputs.poetry2nix.url = "github:nix-community/poetry2nix";
  inputs.poetry2nix.inputs.nixpkgs.follows = "nixpkgs";
  inputs.poetry2nix.inputs.flake-utils.follows = "flake-utils";

  outputs = { self, flake-utils, nixpkgs, poetry2nix }: flake-utils.lib.eachDefaultSystem (system: let
    pkgs = import nixpkgs {
      inherit system;
      overlays = [
        poetry2nix.overlays.default
      ];
    };

    # TODO pull python version from shared single point of truth with pyproject.toml
    pyPackages = pkgs.python312Packages;

    poetryOverrides = pkgs.poetry2nix.defaultPoetryOverrides.extend (final: prev: {
      pytest-depends = prev.pytest-depends.overridePythonAttrs (oa: {
        buildInputs = oa.buildInputs or [] ++ [
          final.setuptools # Build backend
        ];
      });
      steamio = prev.steamio.overridePythonAttrs (oa: {
        buildInputs = oa.buildInputs or [] ++ [
          final.poetry # Build backend
          final.tomli # Replacement for Python 3.11 tomllib
        ];
        propagatedBuildInputs = oa.propagatedBuildInputs or [] ++ [
          # Due to the `betterproto` dependency using pkg_resources
          final.setuptools
        ];
      });
      taskgroup = prev.taskgroup.overridePythonAttrs (oa: {
        buildInputs = oa.buildInputs or [] ++ [
          final.flit-core # Build backend
        ];
      });
      tomli = prev.tomli.overridePythonAttrs (oa: {
        buildInputs = oa.buildInputs or [] ++ [
          final.flit-core # Build backend
        ];
      });
      cryptography = prev.cryptography.overridePythonAttrs(oa: {
        cargoDeps = pkgs.rustPlatform.fetchCargoVendor {
          inherit (oa) src;
          sourceRoot = "${oa.pname}-${oa.version}/src/rust";
          name = "${oa.pname}-${oa.version}";
          hash = "sha256-yZg8HSdDufsIu7vvjdzk/AHSVKkteXmQuoF9jAVJIVY=";
        };
      });
    });
    inherit (pkgs.lib) elem flip;
  in rec {
    devShell = pkgs.mkShell {
      name = "personal-archiver-steam-shell";
      nativeBuildInputs = with pkgs; [
        poetry
        coreutils yj jq gnused # used in .envrc
        # niv
        # pyright

        # Used in integration tests
        postgresql_16
      ];
      shellHook = ''
        export PYTHONPATH="$PWD:$PYTHONPATH"
        # NOTE: See Poetry issues # 1917 and 8761
        export PYTHON_KEYRING_BACKEND="keyring.backends.null.Keyring"
      '';
    };

    packages.default = self.packages.${system}.personal-archiver-steam;
    packages.personal-archiver-steam = (pkgs.callPackage ./nix/package.nix {
      inherit (pyPackages) python;
      inherit (pkgs.poetry2nix) mkPoetryApplication;
      overrides = poetryOverrides;
      src = ./.;
    });

    packages.arxWrapped.personal-archiver-steam = let
      arxCommand = pkgs.callPackage ./nix/arxCommand.nix { inherit (pkgs.haskellPackages) arx; };
    in arxCommand {
      prootClosure = packages.prootClosure.personal-archiver-steam;
      cmd = "personal-archiver-steam";
    };
    packages.prootClosure.personal-archiver-steam = let
      proot = pkgs.callPackage ./nix/prootClosure.nix { };
    in proot { wrapped = packages.personal-archiver-steam; };
    defaultPackage = packages.personal-archiver-steam;
    defaultApp = flake-utils.lib.mkApp {
      name = "personal-archiver-steam";
      drv = defaultPackage;
    };
  });
}
