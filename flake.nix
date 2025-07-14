{
  description = "A development shell with uv and redis";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
  };

  outputs = { self, nixpkgs }:
    let
      supportedSystems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
      forAllSystems = nixpkgs.lib.genAttrs supportedSystems;

    in
    {
      devShells = forAllSystems (system:
        let
          pkgs = import nixpkgs {
            inherit system;
          };
        in
        {
          default = pkgs.mkShell {
            buildInputs = [
              pkgs.uv
              pkgs.python3
              pkgs.redis
              pkgs.datasette
              pkgs.ruff
              pkgs.just
            ];

            shellHook = ''
              if ! pgrep -x "redis-server" > /dev/null
              then
                echo "Starting Redis server in the background..."
                redis-server --daemonize yes
              else
                echo "Redis server is already running."
              fi
              echo "Development environment is ready."
            '';
          };
        });
    };
}
