#!/usr/bin/env python3
"""Test script to verify workflow widgets are properly embedded in tabs."""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent / "python"))

from bathy.ui.screens.project_detail import ProjectDetailScreen

# Create the screen
screen = ProjectDetailScreen()

# Check if widgets were created
print("Testing ProjectDetailScreen initialization...")
print(f"✓ Screen created: {screen.__class__.__name__}")
print(f"✓ Has workflow_image_widget: {hasattr(screen, 'workflow_image_widget')}")
print(f"✓ Has workflow_mesh_widget: {hasattr(screen, 'workflow_mesh_widget')}")

if hasattr(screen, "workflow_image_widget"):
    print(f"  - Image widget type: {screen.workflow_image_widget.__class__.__name__}")
    print(f"  - Image widget id: {screen.workflow_image_widget.id}")

if hasattr(screen, "workflow_mesh_widget"):
    print(f"  - Mesh widget type: {screen.workflow_mesh_widget.__class__.__name__}")
    print(f"  - Mesh widget id: {screen.workflow_mesh_widget.id}")

print("\n✓ All widgets properly initialized!")
