{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = with pkgs; [
    python312
    python312Packages.pip
    python312Packages.virtualenv
    python312Packages.pandas
    python312Packages.pillow
    python312Packages.xarray
    
    # Development tools
    python312Packages.pytest
    python312Packages.black
    python312Packages.flake8
    
    # System dependencies that might be needed
    zlib
    libffi
    openssl
  ];

  shellHook = ''
    echo "Entering Python 3.12 development environment for bathymesh"
    echo "Python version: $(python --version)"
    echo "Available packages: pandas, pillow, xarray"
    echo ""
    echo "You can now run your Python scripts with Python 3.12"
    echo "To install additional packages, use: pip install <package>"
    echo ""
    
    # Create a virtual environment if it doesn't exist
    if [ ! -d ".venv" ]; then
      echo "Creating virtual environment..."
      python -m venv .venv
    fi
    
    # Activate the virtual environment
    source .venv/bin/activate
    
    # Upgrade pip and install project dependencies
    pip install --upgrade pip
    pip install -e .
  '';
}
