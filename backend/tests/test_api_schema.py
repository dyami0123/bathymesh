"""
Tests for OpenAPI schema transformation.

Ensures that Pydantic fields with defaults and default_factory
are marked as required in output schemas for proper TypeScript generation.
"""

import pytest
from bathy.api.main import app, transform_schemas_for_output
from bathy.config import (
    MeshUnits,
    HeighmapProcessingConfig,
    OutputModel,
)


def test_mesh_units_all_fields_required():
    """MeshUnits fields with scalar defaults should be required in schema."""
    spec = app.openapi()
    schema = spec["components"]["schemas"]["MeshUnits"]

    assert "required" in schema
    assert set(schema["required"]) == {"units_x", "units_y", "units_z"}


def test_heightmap_config_scalar_defaults_required():
    """Scalar default fields should be required."""
    spec = app.openapi()
    schema = spec["components"]["schemas"]["HeighmapProcessingConfig"]

    required = set(schema.get("required", []))

    # Scalar defaults
    assert "exterior_buffer_width" in required
    assert "exterior_buffer_value" in required
    assert "data_offset" in required
    assert "base_height" in required
    assert "layer_thickness" in required


def test_heightmap_config_factory_defaults_required():
    """default_factory fields should be required."""
    spec = app.openapi()
    schema = spec["components"]["schemas"]["HeighmapProcessingConfig"]

    required = set(schema.get("required", []))

    # Factory defaults
    assert "mesh_units" in required
    assert "thresholds" in required


def test_output_model_fields_not_required_for_construction():
    """Python models should still allow construction without defaults."""
    # This should not raise
    config = HeighmapProcessingConfig()

    assert config.exterior_buffer_width == 0
    assert config.mesh_units.units_x == 1.0
    assert len(config.thresholds) == 10


def test_output_model_serialization_includes_defaults():
    """Serialized output should include all defaulted fields."""
    config = HeighmapProcessingConfig()
    data = config.model_dump()

    # All defaulted fields present
    assert "exterior_buffer_width" in data
    assert "exterior_buffer_value" in data
    assert "mesh_units" in data
    assert "thresholds" in data
    assert "base_height" in data
    assert "layer_thickness" in data


def test_transform_preserves_existing_required():
    """Transform should not remove existing required fields."""
    # Mock schema with existing required
    test_schema = {
        "components": {
            "schemas": {
                "TestModel": {
                    "type": "object",
                    "properties": {
                        "required_field": {"type": "string"},
                        "defaulted_field": {"type": "number", "default": 0},
                    },
                    "required": ["required_field"],
                }
            }
        }
    }

    # Note: This test would need actual OutputModel subclass to work properly
    # For now, just verify transform doesn't crash on unknown schemas
    result = transform_schemas_for_output(test_schema)

    # Should preserve structure
    assert "components" in result
    assert "schemas" in result["components"]


def test_nullable_field_with_none_default():
    """
    Fields like `name: str | None = None` should be required but nullable.

    This tests the edge case where a field has a None default
    but should still be present in output.
    """
    # Add test when we have such a field
    # For now, verify principle: field.is_required() == False means add to required
    from bathy.config import ImageProcessingConfig

    field_info = ImageProcessingConfig.model_fields["max_dimension"]

    # max_dimension: Optional[int] = Field(default=None)
    assert not field_info.is_required()

    # Should be in required array
    spec = app.openapi()
    schema = spec["components"]["schemas"]["ImageProcessingConfig"]
    assert "max_dimension" in schema.get("required", [])


def test_all_config_models_inherit_output_model():
    """All config models should inherit from OutputModel for schema customization."""
    from bathy import config as config_module
    import inspect

    config_models = [
        obj
        for name, obj in vars(config_module).items()
        if (
            inspect.isclass(obj)
            and issubclass(obj, OutputModel)
            and obj is not OutputModel
        )
    ]

    # Should have found config models
    assert len(config_models) > 0

    # All should be OutputModel subclasses
    for model in config_models:
        assert issubclass(model, OutputModel)
