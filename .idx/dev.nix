# To learn more about how to use Nix to configure your environment
# see: https://firebase.google.com/docs/studio/customize-workspace
{ pkgs, ... }: {
  # Which nixpkgs channel to use.
  channel = "stable-25.05"; # or "unstable"

  # Use https://search.nixos.org/packages to find packages
  packages = [
    pkgs.uv
  ];

  services = {
    docker = {
      enable = true;
    };
  };

  idx = {
    # Search for the extensions you want on https://open-vsx.org/ and use "publisher.id"
    extensions = [
      "charliermarsh.ruff"
      "astral-sh.ty"
      "ms-python.python"
      "ms-python.debugpy"
      "ms-azuretools.vscode-docker"
      "EditorConfig.EditorConfig"
      "usernamehw.errorlens"
      "tamasfe.even-better-toml"
      "Codeium.codeium"
      "castrogusttavo.symbols"
      "antfu.icons-carbon"
      "antfu.file-nesting"
    ];
  };
}
