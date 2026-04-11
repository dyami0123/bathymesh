from typing import get_type_hints
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from bathy.config import ProjectConfig, OutputModel
from bathy.database import DatabaseInterface
import inspect

version: str = "0.1.0"


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


app = FastAPI(title="Bathymesh API", version=version)

# Save original openapi method before override
_original_openapi_method = app.openapi
_cached_openapi = None


def custom_openapi():
    """Generate OpenAPI schema with transformed defaults."""
    global _cached_openapi
    if _cached_openapi is not None:
        return _cached_openapi

    # Call original method to get base schema
    openapi_schema = _original_openapi_method()
    # Transform it
    _cached_openapi = transform_schemas_for_output(openapi_schema)
    return _cached_openapi


app.openapi = custom_openapi

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
    ],  # Vite/React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Bathymesh API", "version": app.version}


@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/api/config/defaults")
async def defaults() -> ProjectConfig:
    return ProjectConfig()


@app.get("/api/config/{project_id}")
async def get_project_config(project_id: str) -> ProjectConfig:
    return DatabaseInterface.get_config(project_id=project_id)


@app.put("/api/config/{project_id}")
async def set_project_config(project_id: str, project_config: ProjectConfig):
    DatabaseInterface.set_config(project_id=project_id, project_config=project_config)


@app.post("/api/config/validate")
async def validate_project_config(project_config: ProjectConfig) -> bool:
    return True


def serve() -> None:
    """Run the API server with local development defaults."""
    import uvicorn

    uvicorn.run(
        "bathy.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    serve()
