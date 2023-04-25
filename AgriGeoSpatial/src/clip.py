import os
import pyproj
import geopandas as gpd
import rasterio as rio
from shapely.geometry import box
import matplotlib.pyplot as plt

def subset_geom(path: str, crs: pyproj.crs.crs.CRS = 'epsg:3763', grid_resolution: int = 20):
    """generate resolution grid_res x grid_rs
    
    Parameters
    ----------
        :path
        :crs
    
    Return 
    ------
    
    """
    # Load the two GeoDataFrames
    gpd_df = gpd.read_file(path)
    original_crs = gpd_df.crs
    
    # convert degrees to meter
    gpd_df = gpd_df.to_crs(crs)

    # Get the bounding box of the shapefile
    xmin, ymin, xmax, ymax = gpd_df.total_bounds
    
    # Calculate the number of rows and columns in the grid based on the resolution
    num_cols = int((xmax - xmin) / grid_resolution)
    num_rows = int((ymax - ymin) / grid_resolution)
    
    # Generate a grid of polygons within the bounding box
    polygons = []
    for row in range(num_rows+2):
        for col in range(num_cols+2):
            x1 = xmin + col * grid_resolution
            y1 = ymin + row * grid_resolution
            x2 = x1 + grid_resolution
            y2 = y1 + grid_resolution
            polygons.append(box(x1, y1, x2, y2))
            
    # Create a GeoDataFrame from the list of polygons
    return gpd.GeoDataFrame(geometry=polygons, crs=crs).to_crs(original_crs)


def clip_with_harvest(geom, yield_path, MinAreaPercentage = 0.6):
    yield_df = gpd.read_file(yield_path)

    # Initialize an empty GeoDataFrame to store the intersections meeting the condition
    valid_geom = []    
    for idx, row in geom.iterrows():
        # # Step 1: Convert the shapely polygon into a GeoSeries
        # row_geoseries = gpd.GeoSeries([row.geometry])

        # Step 1: Create a GeoDataFrame for each row
        # row_gdf = gpd.GeoDataFrame({'geometry': row_geoseries}, crs="epsg:4326")
        row_gdf = gpd.GeoDataFrame(row.to_frame().T, geometry='geometry', crs = ds.rio.crs)
        
        # Step 2: Perform the intersection operation with gdf2
        intersection = gpd.overlay(row_gdf, yield_df, how='intersection')

        # Step 4: Calculate the area of the intersection
        intersection['area'] = intersection.to_crs('epsg:3763').area

        # Step 5: filter out the 20 m x 20 m box if area of the intersection 
        #         ratio is larger than MinAreaPercentage
        if intersection['area'].sum()/400. > MinAreaPercentage:
            # valid_geometry = valid_geometry.append(row, ignore_index=True)
            valid_geom.append(row)
        valid_geom = pd.concat(valid_geom)
        
        valid_geom = valid_geom.reset_index().drop('index',axis=1).rename(columns={0:'geometry'})
        valid_geom_gdf = gpd.GeoDataFrame(valid_geom, geometry = 'geometry',crs='epsg:4326')
        
        sjoin = gpd.sjoin(valid_geom_gdf, yield_df.to_crs('epsg:4326'), how='left', predicate='intersects').dropna()
        return sjoin.groupby('index_right').agg('first')
