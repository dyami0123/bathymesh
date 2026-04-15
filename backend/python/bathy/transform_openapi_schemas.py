from bathy.config import OutputModel
import inspect


def transform_schemas_for_output(openapi_schema: dict) -> dict:
    """
    Transform OpenAPI schemas to mark fields with defaults as required.

    For response/output types, fields with default values should always be present
    after serialization, even though they're optional during construction.

    This function walks through all schemas and inspects the corresponding Python
    models to find fields with default or default_factory, adding them to the
    'required' array for proper TypeScript generation.
    """
    # Build map of schema name to Python class
    # Import all config models
    import sys
    from bathy import config as config_module

    model_map = {}
    for name in dir(config_module):
        obj = getattr(config_module, name)
        if (
            inspect.isclass(obj)
            and issubclass(obj, OutputModel)
            and obj is not OutputModel
        ):
            model_map[obj.__name__] = obj

    schemas = openapi_schema.get("components", {}).get("schemas", {})

    for schema_name, schema in schemas.items():
        if schema.get("type") != "object":
            continue

        # Get corresponding Python model
        # FastAPI may append -Input or -Output suffix
        base_name = schema_name.removesuffix("-Input").removesuffix("-Output")
        model_class = model_map.get(base_name)
        if not model_class:
            # Try exact match
            model_class = model_map.get(schema_name)
        if not model_class:
            continue

        properties = schema.get("properties", {})
        if not properties:
            continue

        # Find fields with defaults or default_factory
        defaulted_props = []
        for field_name, field_info in model_class.model_fields.items():
            # Use serialization name (alias if present)
            prop_name = field_info.serialization_alias or field_info.alias or field_name

            # Check if field has default or default_factory
            if not field_info.is_required():
                defaulted_props.append(prop_name)

        if defaulted_props:
            # Add to required array, preserving existing required fields
            existing_required = schema.get("required", [])
            # Combine and deduplicate
            all_required = list(set(existing_required + defaulted_props))
            schema["required"] = sorted(all_required)

    return openapi_schema
