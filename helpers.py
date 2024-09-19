import numpy as np
import rasterio
from rasterio.transform import from_origin
from scipy import ndimage

def calculate_diversity(df):
    """
    Calculates the Shannon Diversity Index for a DataFrame containing species occurrences.
    """
    total_count = len(df)
    species_counts = df['unit.linkings.taxon.id'].value_counts()
    proportions = species_counts / total_count
    shannon_diversity = -sum(proportions * np.log(proportions)) # Shannon diversity
    return shannon_diversity

def heatmap(gdf, bins=(100,100), smoothing=1, weight_col=None):
    """
    Creates a normalized heatmap

    Parameters:
    gdf (GeoDataFrame): The geodataframe containing point data
    bins (Integer or Tuple): The number of bins for the 2D histogram grid (default is (100, 100)), which defines the resolution of the heatmap.
    smoothing (Float): A parameter for Gaussian smoothing applied to the heatmap.
    weight_col (String): The column in the GeoDataFrame used to weight the points when generating the heatmap.
    """
    x = gdf.geometry.x
    y = gdf.geometry.y

    # Get weights
    weights = gdf[weight_col] if weight_col else None

    # Create a 2d histogram
    heatmap, xedges, yedges = np.histogram2d(x, y, bins=bins, weights=weights)

    # Create logarithmic values
    logheatmap = np.log(heatmap + 1) # Add one to avoid log(0)
    logheatmap[np.isneginf(logheatmap)] = 0
    logheatmap = ndimage.filters.gaussian_filter(logheatmap, smoothing, mode='nearest') #

    # Normalize heatmap values to the range [0, 1]
    min_val = np.min(logheatmap)
    max_val = np.max(logheatmap)
    if max_val > min_val:
        normalized_heatmap = (logheatmap - min_val) / (max_val - min_val)
    else:
        normalized_heatmap = logheatmap  # Keep the same when all values are the same

    # Replace small values with nans
    normalized_heatmap[normalized_heatmap < 0.01] = np.nan

    return xedges, yedges, normalized_heatmap

def save_heatmap(xedges, yedges, logheatmap, crs, output_file='output_heatmap.tif'):
    """
    Save the heatmap as a GeoTIFF raster file  

    Parameters:
    - xedges: Array of x-axis bin edges.
    - yedges: Array of y-axis bin edges.
    - logheatmap: 2D numpy array representing the heatmap data (logarithmically scaled).
    - crs: Coordinate reference system.
    - output_file: Name of the output GeoTIFF file (default is 'output_heatmap.tif').
    """

    # Transpose and flip the raster
    flipped_heatmap = np.flipud(np.transpose(logheatmap))
    transform = from_origin(xedges[0], yedges[-1], np.diff(xedges)[0], np.diff(yedges)[0])

    with rasterio.open(
        output_file, 'w',
        driver='GTiff',
        height=flipped_heatmap.shape[0],
        width=flipped_heatmap.shape[1],
        count=1,
        dtype=flipped_heatmap.dtype,
        crs=crs,
        transform=transform
    ) as dst:
        dst.write(flipped_heatmap, 1)

        # Add overviews (pyramids) for better performance 
        dst.build_overviews([2, 4, 8, 16], resampling=rasterio.enums.Resampling.average)
        dst.update_tags(ns='rio_overview', resampling='average')

    print(f"Heatmap saved as {output_file}")    