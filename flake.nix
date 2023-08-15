{
  description = "poetry2nix packaging for personal-archiver-steam";

  inputs.flake-utils.url = "github:numtide/flake-utils";
  inputs.nixpkgs.url = "nixpkgs";
  inputs.poetry2nix.url = "github:nix-community/poetry2nix";
  inputs.poetry2nix.inputs.nixpkgs.follows = "nixpkgs";

  outputs = { self, flake-utils, nixpkgs, poetry2nix }: flake-utils.lib.eachDefaultSystem (system: let
    pkgs = import nixpkgs {
      inherit system;
      overlays = [
        poetry2nix.overlay
      ];
    };

    # TODO pull python version from shared single point of truth with pyproject.toml
    pyPackages = pkgs.python310Packages;

    poetryOverrides = pkgs.poetry2nix.overrides.withDefaults (self: super: {
      pytest-depends = super.pytest-depends.overridePythonAttrs (oa: {
        buildInputs = oa.buildInputs or [] ++ [
          super.setuptools
        ];
      });
      steamio = super.steamio.overridePythonAttrs (oa: {
        buildInputs = oa.buildInputs or [] ++ [
          super.poetry
        ];
        propagatedBuildInputs = oa.propagatedBuildInputs or [] ++ [
          # Due to the `betterproto` dependency using pkg_resources
          super.setuptools
        ];
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
        postgresql_15
      ];
      shellHook = ''
        export PYTHONPATH="$PWD:$PYTHONPATH"
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