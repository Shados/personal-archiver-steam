{ runCommand, lib, closureInfo, pkgsStatic, fetchFromGitHub
, writeScript, nix, makeWrapper, gnused
}:
with lib;
args@{wrapped, ...}:
let
  proot = (pkgsStatic.proot.override { enablePython = false; }).overrideAttrs(oa: {
    version = "2020-02-16";
    src = fetchFromGitHub {
      owner = "proot-me"; repo = "proot";
      rev = "f421d8f4c4029687b7b1dbf3305f4cf5b5cb7152";
      sha256 = "0ddwf703i3x70bh55xlcjm1ml5k839ylj45a3xg7zlx1d0x9nfc8";
    };
    patches = singleton ./proot_seccomp.patch;
  });
  drvArgs = filterAttrs (name: _val: !elem name [
      "wrapped"
    ]) args;
in
runCommand "proot-closure-${wrapped.name}" (rec {
  allowSubstitutes = false;
  preferLocalBuild = true;
  inherit proot;
  patchShebangs = false;
  buildInputs = [
    nix makeWrapper gnused
  ];

  wrappedPath = wrapped;
  wrappedClosure = closureInfo { rootPaths = singleton wrapped; };

  wrappedBinWrapper = writeScript "wrapper" ''
    #!/usr/bin/env bash
    ROOT_DIR=$(
      cd "$(dirname "''${BASH_SOURCE[0]}")" || exit 1
      cd .. || exit 1
      pwd
    )
    "$ROOT_DIR/bin/proot" -b "$ROOT_DIR/nix:/nix" "@WRAPPED@" "''${@}"
  '';
} // args) ''
  mkdir -p "bin"
  cp $proot/bin/proot "bin/"

  # Copy closure's store paths
  mkdir -p nix/store
  for i in $(< $wrappedClosure/store-paths); do
    echo "Copying $i"
    cp -a "$i" "''${i:1}"
  done

  echo "Wrapping binaries"
  (
    cd "bin"
    for binPath in $wrappedPath/bin/*; do
      bin="$(basename "$binPath")"
      cp "$wrappedBinWrapper" "./$bin"
      substituteInPlace "./$bin" \
        --subst-var-by WRAPPED "$binPath"
    done
  )

  echo "Moving to output"
  chmod -R +w bin nix
  mkdir -p $out
  mv bin nix $out/
''

