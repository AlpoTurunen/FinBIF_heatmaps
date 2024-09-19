import geopandas as gpd
import pandas as pd
import requests

def get_last_page(data_url):
    """
    Get the last page number from the API response.

    Parameters:
    data_url (str): The URL of the API endpoint.

    Returns:
    int: The last page number.
    """
    try:
        response = requests.get(data_url)
        api_response = response.json()
        last_page = api_response.get("lastPage")
        return last_page
    except Exception as e:
        print("An error occurred when getting the last page of api results. Perhaps JSON file is invalid. Returning only the first page.")
        raise e

def download_page(data_url, page_no):
    """
    Download data from a specific page of the API. This is in separate function to speed up multiprocessing.

    Parameters:
    data_url (str): The URL of the API endpoint.
    page_no (int): The page number to download.

    Returns:
    geopandas.GeoDataFrame: The downloaded data as a GeoDataFrame.
    """
    # Load data
    data_url = data_url.replace('page=1', f'page={page_no}')
    gdf = gpd.read_file(data_url)  
    #print(gdf.columns)
    #gdf = gdf[['unit.unitId', 'geometry']]  
    return gdf

def get_occurrence_data(data_url, startpage = 1, pages=10):
    """
    Retrieve occurrence data from the API.

    Parameters:
    data_url (str): The URL of the API endpoint.
    pages (str or int, optional): Number of pages to retrieve. Defaults to "all".

    Returns:
    geopandas.GeoDataFrame: The retrieved occurrence data as a GeoDataFrame.
    """

    if pages == 'all':
        endpage = get_last_page(data_url)
        print(f"Loading {endpage} pages..")
    else:
        endpage = int(pages)
    
    gdf = gpd.GeoDataFrame()

    for page_no in range(startpage,endpage+1):
        next_gdf = download_page(data_url, page_no)
        #next_gdf = next_gdf[next_gdf.geom_type.isin(['Polygon', 'MultiPolygon', 'GeometryCollection'])]
        gdf = pd.concat([gdf, next_gdf], ignore_index=True)
        print(f"Page {page_no} downloaded")

    return gdf