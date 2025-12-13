import xarray as xr
import numpy as np


path = "data/raw/mhi_mbsyn_bathytopo_1km_v21.nc"
save_path = "data/processed/hawaii_full.npy"


ds = xr.load_dataset(path)

z = ds.z
z_np_array = z.to_numpy()

min_value = np.nanmin(z_np_array)
max_value = np.nanmax(z_np_array)

print(f"Min value: {min_value}")
print(f"Max value: {max_value}")

np.save(save_path, z_np_array)