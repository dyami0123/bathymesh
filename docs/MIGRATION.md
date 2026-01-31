# Bathymesh Configuration Migration Guide

## NumPy Scalar Serialization Fix (v0.2.0)

### Issue
Prior to v0.2.0, mesh configuration files saved `thresholds` as numpy scalar objects, which resulted in unreadable YAML like:

```yaml
thresholds:
  - !!python/object/apply:numpy._core.multiarray.scalar
    - &id001 !!python/object/apply:numpy.dtype
      args: [f8, false, true]
    - !!binary |
      AAAAAAAAAAA=
```

### Fix
As of v0.2.0, thresholds are now properly saved as Python floats:

```yaml
thresholds:
  - 0.0
  - 5.555555555555555
  - 11.11111111111111
  - 16.666666666666664
```

### Migration

If you have existing project configurations with numpy scalar objects:

**Option 1: Delete and Recreate (Recommended)**
```bash
# Delete the config file
rm ~/bathymesh_projects/my-project/mesh_config.yaml

# The TUI will automatically recreate it with defaults next time you open the project
```

**Option 2: Manual Edit**
Open the YAML file and replace the numpy scalar blocks with plain numbers.

### Error Message
If you try to load an old config, you'll see:
```
ConfigIOError: Config file contains numpy scalar objects that cannot be loaded. 
This may be from an older version. Please delete the config file and it will be 
recreated with correct format.
```

### Prevention
All new configs saved after v0.2.0 will automatically use proper Python float serialization. The fix is applied in `config_io.py`:

```python
# When saving:
"thresholds": [float(x) for x in config.heightmap_processing.thresholds],

# When loading:
thresholds_raw = hp_data.get("thresholds", [...])
thresholds = [float(x) for x in thresholds_raw]
```

This ensures that numpy scalars are converted to regular Python floats during serialization and deserialization.
