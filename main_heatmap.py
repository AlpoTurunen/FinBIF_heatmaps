import geopandas as gpd
import numpy as np
import os
from shapely.geometry import Point
from load_data import get_occurrence_data
from helpers import calculate_diversity, heatmap, save_heatmap
from dotenv import load_dotenv

def main():

    load_dotenv()
    access_token = os.getenv('ACCESS_TOKEN')

    # Prompt the user for input with default values
    municipal_id = input("Enter municipal_id (e.g., 'ML.660' for Helsinki): ") or 'ML.660'
    informal_taxon_ids = input("Enter informal_taxon_ids (e.g., 'MVL.2' for mammals). You can add many: ") or 'MVL.2'
    time = input("Enter time after which occurrences will be loaded (e.g., '2010-01-01'): ") or '2010-01-01'
    grid_size = input("Enter grid size of the output heatmap in meters (e.g. 100): ") or 100
    grid_size = int(grid_size)

    # Print the inputs for confirmation
    print(f"\nCreating an heatmap using the following parameters:")
    print(f"Municipal ID: {municipal_id}")
    print(f"Informal Taxon IDs: {informal_taxon_ids}")
    print(f"Time: {time}")
    print(f"Grid size: {grid_size}")

    file_basename = f'{municipal_id}_{informal_taxon_ids}_{time}'.replace('.', '_')

    # Check if the data exists 
    if os.path.exists(f'{file_basename}_data.json'):
        print(f"Using local data {file_basename}_data.json")
        gdf = gpd.read_file(f'{file_basename}_data.json')
    else:
        api_url = f'https://api.laji.fi/v0/warehouse/query/unit/list?selected=unit.taxonVerbatim,unit.linkings.taxon.id,unit.linkings.taxon.scientificName&informalTaxonGroupId={informal_taxon_ids}&page=1&pageSize=10000&coordinateAccuracyMax=500&time={time}/&geoJSON=true&featureType=CENTER_POINT&finnishMunicipalityId={municipal_id}&access_token={access_token}' 
        gdf = get_occurrence_data(api_url, pages="all")
        #gdf.to_file(f'{file_basename}_data.json', driver='GeoJSON') # Uncomment if you want to use same data again and again

    gdf = gdf.to_crs(3067)

    if len(gdf) < 1000:
        print(f"Warning: the heatmap will be generated only from {len(gdf)} occurrences")

    # Define grid size for bounding box
    x_min, y_min, x_max, y_max = gdf.total_bounds
    extent_width = x_max - x_min
    extent_height = y_max - y_min

    x_edges = np.arange(x_min, x_max, grid_size)
    y_edges = np.arange(y_min, y_max, grid_size)

    # Assign each occurrence point to a grid cell
    gdf['grid_x'] = np.digitize(gdf.geometry.x, x_edges)
    gdf['grid_y'] = np.digitize(gdf.geometry.y, y_edges)

    # Group by grid cells and calculate Shannon Diversity Index for each cell
    diversity_data = gdf.groupby(['grid_x', 'grid_y'], as_index=True).apply(calculate_diversity).reset_index()
    diversity_data = diversity_data.rename(columns={0: "shannon_diversity"})

    # Calculate grid cell centroids and create geometries
    diversity_data['x_centroid'] = x_edges[diversity_data['grid_x'] - 1] + grid_size / 2
    diversity_data['y_centroid'] = y_edges[diversity_data['grid_y'] - 1] + grid_size / 2

    # Create geometries using centroids
    diversity_data['geometry'] = diversity_data.apply(lambda row: Point(row['x_centroid'], row['y_centroid']), axis=1)

    # Convert to GeoDataFrame
    gdf_diversity = gpd.GeoDataFrame(diversity_data, geometry='geometry', crs=gdf.crs)
    gdf_diversity = gdf_diversity.drop(columns=['grid_x', 'grid_y'])

    # Get heatmap pixel size
    bins = (int(extent_width // grid_size), int(extent_height // grid_size))
    
    # Create a heatmap
    xedges, yedges, normalized_heatmap = heatmap(gdf_diversity, bins=bins, smoothing=1, weight_col='shannon_diversity')

    # Save the heatmap
    crs = gdf_diversity.crs.to_string()
    save_heatmap(xedges, yedges, normalized_heatmap, crs, output_file=f'{file_basename}_heatmap.json')

if __name__ == "__main__":
    main()
