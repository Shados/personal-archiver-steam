{ lib, runCommand, writeScript
, arx
}:
with lib;
args@{ prootClosure, cmd }:
let
  runArgs = filterAttrs (name: _val: !elem name [ "prootClosure" "cmd" ] ) args;
  arx' = arx.overrideAttrs (o: {
    patchPhase = (o.patchPhase or "") + ''
      substituteInPlace model-scripts/tmpx.sh \
        --replace /tmp/ \$HOME/.cache/
    '';
  });
in
runCommand "arx-${prootClosure.name}" (rec {
  allowSubstitutes = false;
  preferLocalBuild = true;
}) ''
  echo "Tarballing input closure"
  tarball="$PWD/wrapped.tar.gz"
  (
    cd "${prootClosure}"
    tar --owner=0 --group=0 --mode=u+rw,uga+r --hard-dereference -cvzf "$tarball" bin nix
  )

  echo "Creating arx output"
  ${arx'}/bin/arx tmpx --shared "$tarball" -o $out // './bin/${cmd} $@'
  chmod +x $out
''
