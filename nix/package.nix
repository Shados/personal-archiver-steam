{ lib, mkPoetryApplication, python, doCheck ? true, overrides, src }:
with lib;
let
  pyproject = src + /pyproject.toml;
  metadata = (builtins.fromTOML (builtins.readFile pyproject)).tool.poetry;
in
mkPoetryApplication rec {
  inherit src python doCheck pyproject overrides;
  poetrylock = src + /poetry.lock;

  meta = {
    maintainers = metadata.maintainers or metadata.authors;
    description = metadata.description;
  } // optionalAttrs (metadata ? repository) { downloadPage = metadata.repository; };
}
