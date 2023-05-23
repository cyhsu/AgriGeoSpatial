import os
import geopandas as gpd
import rasterio
import tempfile
import zipfile
import pyproj
import pandas as pd
from datetime import datetime
from shapely.geometry import box, Polygon
import matplotlib.pyplot as plt
import re


class GeoFileProcessor:
    def __init__(self, directory, keyword):
        self.directory = directory
        self.keyword = keyword
        self.shp_files = []
        self.zip_files = []
        self.tif_files = {}

    def collect_file_path(self):
        for dirname, _, filenames in os.walk(self.directory):
            if self.keyword in dirname:
                for filename in filenames:
                    file_path = os.path.join(dirname, filename)

                    # Collect .shp file paths
                    if filename.endswith(".shp"):
                        self.shp_files.append(file_path)

                    # Collect .zip file paths
                    elif filename.endswith(".zip"):
                        self.zip_files.append(file_path)

                    # Collect .tif file paths
                    elif filename.endswith(".tif"):
                        # Extract the date from the filename (assuming it is in YYYYMMDD format)
                        date_match = re.search(r"\d{4}-\d{2}-\d{2}", dirname)
                        if date_match:
                            date = date_match.group()
                            if (self.keyword, date) in self.tif_files:
                                self.tif_files[(self.keyword, date)].append(file_path)
                            else:
                                self.tif_files[(self.keyword, date)] = [file_path]

            else:
                for filename in filenames:
                    if self.keyword in filename:
                        file_path = os.path.join(dirname, filename)

                        # Collect .shp file paths
                        if filename.endswith(".shp"):
                            self.shp_files.append(file_path)

                        # Collect .zip file paths
                        elif filename.endswith(".zip"):
                            self.zip_files.append(file_path)

    def subset_geom(
        path: str, crs: pyproj.crs.crs.CRS = "epsg:3763", grid_resolution: int = 20
    ):
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
        for row in range(num_rows + 2):
            for col in range(num_cols + 2):
                x1 = xmin + col * grid_resolution
                y1 = ymin + row * grid_resolution
                x2 = x1 + grid_resolution
                y2 = y1 + grid_resolution
                polygons.append(box(x1, y1, x2, y2))

        # Create a GeoDataFrame from the list of polygons
        return gpd.GeoDataFrame(geometry=polygons, crs=crs).to_crs(original_crs)


# Usage:
path_reader = GeoFileProcessor("../data", "Plei")
path_reader.collect_file_path()

print(path_reader.shp_files)
print(path_reader.zip_files)
print(path_reader.tif_files)
