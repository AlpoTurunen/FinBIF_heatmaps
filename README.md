# FinBIF_heatmaps
FinBIF data to heatmaps

This Python script generates a biodiversity heatmap based on species occurrence data from Finnish Biodiversity Information Facility (FinBIF). It queries the REST API, processes the data, calculates the Shannon Diversity Index for grid cells within a specified municipality, and produces a heatmap as an JSON format.

## How to use
1. Install requirements
   'pip install requirements.txt'

2. Run the code

- Valid input values can be found from api.laji.fi (Area and InformalTaxonGroup endpoints).
- Note, the output heatmap can be more or less empty depending on our input parameters. Include enough taxas, use bigger municipality or bigger timescale or grid size.
