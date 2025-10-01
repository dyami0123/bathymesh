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
            pythonPackages.pip
            pythonPackages.virtualenv
            pythonPackages.pandas
            pythonPackages.pillow
            pythonPackages.xarray
            
            # Development tools
            pythonPackages.pytest
            pythonPackages.black
            pythonPackages.flake8
            pythonPackages.mypy
            
            # System dependencies
            zlib
            libffi
            openssl
            
            # Additional tools that might be useful
            git
            curl
            wget
          ];

          shellHook = ''
            echo "🐍 Bathymesh Development Environment"
            echo "Python version: $(python --version)"
            echo "Location: $(which python)"
            echo ""
            echo "Available packages:"
            echo "  - pandas (data manipulation)"
            echo "  - pillow (image processing)"
            echo "  - xarray (labeled arrays)"
            echo ""
            echo "Development tools:"
            echo "  - pytest (testing)"
            echo "  - black (code formatting)"
            echo "  - flake8 (linting)"
            echo "  - mypy (type checking)"
            echo ""
            
            # Set up virtual environment
            if [ ! -d ".venv" ]; then
              echo "Creating Python virtual environment..."
              python -m venv .venv
            fi
            
            echo "Activating virtual environment..."
            source .venv/bin/activate
            
            # Install the project in development mode
            echo "Installing project dependencies..."
            pip install --upgrade pip
            pip install -e .
            
            echo ""
            echo "✅ Environment ready! You can now work on your bathymesh project."
            echo "To exit this environment, type 'exit' or press Ctrl+D"
          '';

          # Environment variables
          PYTHONPATH = "${python}/${python.sitePackages}";
        };
      });
}
