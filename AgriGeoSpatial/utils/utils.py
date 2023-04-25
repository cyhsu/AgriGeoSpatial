import numpy as np
import rioxarray as rx
import xarray as xr
from scipy.ndimage import gaussian_filter


def shadow_detection(filepath: str) -> xr.Dataset:
    # Load the raster image
    dataset = rx.open_rasterio(filepath)

    # Read the bands
    red_band = dataset.sel(band=1).astype(np.float32)
    green_band = dataset.sel(band=2).astype(np.float32)
    blue_band = dataset.sel(band=3).astype(np.float32)
    nir_band = dataset.sel(band=4).astype(np.float32)

    # Calculate NDVI
    ndvi = (nir_band - red_band) / (nir_band + red_band)

    # Set an NDVI threshold value for shadow detection (e.g., 0.1)
    shadow_threshold = 0.1

    # Identify shadow pixels
    shadow_pixels = ndvi < shadow_threshold

    # Apply a Gaussian filter to the non-shadow pixels of each band
    filtered_red = gaussian_filter(red_band, sigma=3)
    filtered_green = gaussian_filter(green_band, sigma=3)
    filtered_blue = gaussian_filter(blue_band, sigma=3)

    # Correct shadow pixels using the mean value of the surrounding pixels
    corrected_red = np.where(shadow_pixels, filtered_red, red_band)
    corrected_green = np.where(shadow_pixels, filtered_green, green_band)
    corrected_blue = np.where(shadow_pixels, filtered_blue, blue_band)

    # Create a new xarray DataArray for each corrected band
    corrected_red_da = dataset.sel(band=1).copy(data=corrected_red)
    corrected_green_da = dataset.sel(band=2).copy(data=corrected_green)
    corrected_blue_da = dataset.sel(band=3).copy(data=corrected_blue)

    # Replace the original bands with the corrected ones
    corrected_dataset = dataset.copy()
    corrected_dataset.loc[dict(band=1)] = corrected_red_da
    corrected_dataset.loc[dict(band=2)] = corrected_green_da
    corrected_dataset.loc[dict(band=3)] = corrected_blue_da

    return corrected_dataset


def relative_value_of_aerial(geom: gpd.GeoDataFrame, ds: xr.Dataset, percential: float):
    process = []
    for idx, row in geom.iterrows():
        row_gdf = gpd.GeoDataFrame(row.to_frame().T, geometry='geometry', crs = ds.rio.crs)
        clipped = ds.rio.clip(row_gdf.geometry.apply(lambda x: x.__geo_interface__), row_gdf.crs)
        
        ref = clipped.quantile(percential, dim=['x', 'y'])
        rlt = clipped/ref
        row_gdf['band1'], row_gdf['band2'], row_gdf['band3'], row_gdf['band4'] = zip(rlt.mean(dim=['x','y']).data)
        
        process.append(row_gdf)
        
    return pd.concat(process)
    
