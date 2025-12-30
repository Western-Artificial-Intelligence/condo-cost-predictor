# Overview 

This folder contains the first iteration of the data curated from multiple sources to create a comprehensive dataset on neighborhood rental statistics from Open Toronto Datasets and the Toronto Real Estates Board.

## Files Used

- [Toronto 158 neighbourhoods](https://open.toronto.ca/dataset/neighbourhoods/) As GeoJSON file.
- [TTC Bus Transit Data](https://open.toronto.ca/dataset/ttc-routes-and-schedules/)'s `shapes.txt`, `stops.txt`, `stop_times.txt`, `trips.txt` and `route.txt`.
- [Neighborhood crime rates](https://open.toronto.ca/dataset/neighbourhood-crime-rates/) as a GeoJSON file.
- [parks & recreational locations](https://open.toronto.ca/dataset/parks-and-recreation-facilities/) as a GeoJSON file.
- [target variable based on neighborhood region](https://trreb.ca/market-data/rental-market-report/rental-market-report-archive/) was manually extracted from the report file on page 3 for average lease rate and total number of units leased in Q3 2025. 


## File Tree 

```
.
└── data/
    ├── venv # virtual env, not tracked 
    ├── central_neighborhoods.py # intermediate lists of central neighborhoods
    ├── data-pipeline.ipynb # joins 
    ├── data-reqs.txt # dependencies for a virtual environment 
    ├── east_neighborhoods.py # intermediate lists of east neighborhoods 
    ├── extract_content.ipynb # script for extracting the target variable
    ├── neighborhood_lists.ipynb # used to check the target variable 
    ├── postgres.md # previous postgreSQL instructions 
    ├── README.md
    ├── tor_neighborhood_condorental.csv 
    ├── tor_neighborhood_condorental.parquet
    └── west_neighborhoods.py # intermediate lists of west neighborhoods 
```

# Data Join Process 

1. Created a non-persistent schema, `analytics` to create and do joins with.
2. Created a neighborhoods table for the 158 neighborhoods GeoJSON file.
3. Classified all 158 regions (using `neighborhood_lists.ipynb` to check) into the format following TREB's report.
4. Created the manually extracted CSV from the TREB report pdf into target variable table.
5. Left Joined the target variables onto the (main) neighborhoods table to label each neighborhood as a region (ie. Toronto C10).
6. Left Joined the target variables onto the (main) labelled neighborhoods table.
7. Added total area in square meters and perimeter in meters for each neighborhood using `geometry_wkt`.
8. Created the parks table and did a spatial join for number of parks within each neighborhood using `ST_Intersects()`.
9. Created the crime table (~200 cols).
10. Checked `AREA_NAME` on the crime table against `AREA_NAME` in the cumulatively joined neighborhoods table to see if all neighborhood labels matched.
11. All labels matched, so left joined all values from the crime table excluding `_id` and `HOOD_ID` onto the (main) cumulative neighborhoods table (`ON t1.AREA_NAME = t2.AREA_NAME;`)
12. Created the `transit_lines` table from `shapes.txt` for shapes of the routes for bus data, contains geometry data each of the routes.
13. Created the `routes` table from `routes.txt` for bus routes metadata.
14. Created the `trips` table from `trips.txt` for bus trips.
15. Created the `stop_times` table from `stop_times.txt` for bus stop times.
16. Created the `stops` table from `stops.txt` for bus stops metadata.
17. Created the `transit_stops` table from the `stops` table for the geometry objects of the stops, keeps every original column except for longitude and latitude.
18. Created a `line_lookup` table by joining the `routes` and `trips` table on `route_id` with distinct `shape_id`s and the route short name (ie. route 90)
19. Created a `stop_lookup` table using the `stop_times` table for total number of stops made per day via `COUNT(trip_id)`, since every element is a stop made.
20. Joined `transit_stops` and `stop_lookup` tables with (main) the cumulative neighborhood table for stop data enrichment to create `total_stop_count` from the `transit_stops` table, `avg_stop_frequency` from the `stop_lookup` table, and `max_stop_frequency` (max number of stops per day from `stop_lookup`). Used a spatial join on the `transit_stops` table using `ST_Intersects()` and a regular Left Join for `stop_lookup` where the `stop_id`s of both tables matched.
21. Joined `transit_lines` and `line_lookup` tables with (main) cumulative neighborhood table for the spatial data of the bus routes, to create `total_line_length_meters` (total length of bus line(s) within the neighborhood in meters), `transit_line_density` (total length of the line(s) divided by area of the neighborhood, `area_sq_meters`), and `distinct_route_count` (number of unique routes within the neighborhood). Used a spatial join on the `transit_lines` table using `ST_Intersects()` for `total_line_length_meters` and `transit_line_density`, and a Left Join for `transit_lines` where both the `shape_id`s of the tables matched.
22. exported the final table with target variable, park data, crime data and bus transit data.

# Suggested Feature Engineering Strategies 

1. drop the `geometry_type`, `geometry_wkt_1` and `geometry_wkt` columns. They consist of long strings for geometry data.
2. drop any `ID`s and `CODE`s that are not needed.
3. `data-pipeline.ipynb` guarantees that the data type of all valid entries for a column are either `VARCHAR` (String), `INT`, `BIGINT` or `DOUBLE`. Nulls and outliers were not validated against due to potentially being outliers or useful signals for the feature engineering strategy.
4. the target variables, `Bachelor Leased`, `bachelor_avg_leas_rate`, `1_bedrooms_leased`, `1_bedroom_avg_leas_rate`, `2_bedrooms_leased`, `2_bedrooms_avg_leas_rate`, `3_bedrooms_leased`, `3_bedrooms_avg_lease_rate`, contains 0s for some of the columns of total units leased, and consequently a 0 for the average leas rate for some regions, due to missing or incomplete data from the TREB dataset. We can consider dropping the missing target varibles, imputing them, or training a regression model to predict the lease rate and average lease rate for the missing entries. In the meantime, please use this dataset's target variable as an intermediate dataset to decide next concrete steps.
5. the target variables were joined using `Region_classif`. If the model takes in longitude and latitude in production, you need to determine whether the unit belongs to either one of those regions using `ST_INTERSECT()` or checking the `geometry_wkt` (not `geometry_wkt_1`) of the unit. For training, One-Hot-Encode the classifications for each neighborhood's region classification.

# Next Steps 

1. Find more high quality target variables.
2. Curate temporal data for potential time series training.
3. Integrate other crime datasets.
4. Integrate demographic datasets, such as macro data and socioeconomic data.
5. Set up data versioning with DVC and experiment with data.
6. Additional data enrichment/feature creation for the existing spatial joins.
7. Set up DVC pipelines for reproducibility.

# Running Joins 

To run JOINs using DuckDB and Pandas on `data-pipeline.ipynb`, make sure you have one of the following installed:

- Python 3+ and `pip`
- (suggested) [uv](https://docs.astral.sh/uv/getting-started/installation/)

1. `cd data`
2. run `uv venv venv` or `python -m venv venv` to make your virtual environment. Please name the virtual environment `venv` for the `.gitignore` to work.
3. activate it using `source venv/bin/activate`.
4. download the source datasets listed above and place them into a directory called `source-files` inside `data`, the current directory. Place the unzipped `txt` files for TTC bus data inside `source-files/busdata/`. Please make sure the names are correct for the `.gitignore` to work, check `.gitignore` for more details.
5. start the notebook using: `jupyter notebook` in your terminal. You can then run notebook chunks in your browser.

