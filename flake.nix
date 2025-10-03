{
  description = "Bathymesh development environment with Python 3.12";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        python = pkgs.python312;
        pythonPackages = python.pkgs;
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            python
            uv
            
            # System dependencies
            zlib
            libffi
            openssl
            mesa
            zstd
            # libtensorflow
            libGL
            xorg.libX11
            xorg.libXext
            xorg.libXi
            xorg.libXrender
            xorg.libXfixes
            xorg.libXcursor
            xorg.libXrandr
            
            # C++ runtime libraries
            gcc-unwrapped.lib
            stdenv.cc.cc.lib
            
            # Additional system libraries
            udev
            
            # Additional tools that might be useful
            git
            curl
            wget
          ];

          shellHook = ''
            echo "🐍 Bathymesh Development Environment"
            echo "Python version: $(python --version)"
            echo "Location: $(which python)"
            echo "UV version: $(uv --version)"
            echo ""
            echo "Using UV for fast Python package management"
            echo ""
            echo "Available commands:"
            echo "  - uv sync          (install dependencies)"
            echo "  - uv add <package> (add new dependency)"
            echo "  - uv run <script>  (run with dependencies)"
            echo "  - uv shell         (activate virtual environment)"
            echo ""
            
            # Use UV to sync dependencies if pyproject.toml exists
            if [ -f "pyproject.toml" ]; then
              echo "Syncing dependencies with UV..."
              uv sync
            fi
            
            echo ""
            echo "✅ Environment ready! You can now work on your bathymesh project."
            echo "UV will manage your virtual environment and dependencies."

            echo "To exit this environment, type 'exit' or press Ctrl+D"
          '';

          # Environment variables
          PYTHONPATH = "${python}/${python.sitePackages}";
          LD_LIBRARY_PATH = with pkgs; lib.makeLibraryPath [
            zlib
            libffi
            openssl
            mesa
            zstd
            libGL
            xorg.libX11
            xorg.libXext
            xorg.libXi
            xorg.libXrender
            xorg.libXfixes
            xorg.libXcursor
            xorg.libXrandr
            gcc-unwrapped.lib
            stdenv.cc.cc.lib
            udev
          ];
          
        };
      });
}
