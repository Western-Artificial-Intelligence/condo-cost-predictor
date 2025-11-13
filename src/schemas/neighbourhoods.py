"""Schema for neighbourhoods table."""
import pandera as pa
from pandera import Column, DataFrameSchema, Check

# Toronto bounding box (approximate)
TORONTO_LAT_MIN = 43.58
TORONTO_LAT_MAX = 43.86
TORONTO_LON_MIN = -79.64
TORONTO_LON_MAX = -79.12

NeighbourhoodsSchema = DataFrameSchema(
    {
        "id": Column(
            int,
            checks=[
                Check.greater_than(0),
                Check(lambda s: s.is_unique, error="Duplicate neighbourhood IDs found")
            ],
            nullable=False,
            description="Unique neighbourhood identifier"
        ),
        "name": Column(
            str,
            checks=[
                Check.str_length(min_value=1, max_value=100),
                Check(lambda s: s.is_unique, error="Duplicate neighbourhood names found")
            ],
            nullable=False,
            description="Neighbourhood name"
        ),
        "geometry": Column(
            str,  # WKT or GeoJSON string
            nullable=True,  # May be missing for some neighbourhoods
            description="Geographic boundary (WKT/GeoJSON)"
        ),
        "area_km2": Column(
            float,
            checks=[
                Check.greater_than(0),
                Check.less_than(100)  # Toronto neighbourhoods typically < 100 km²
            ],
            nullable=False,
            description="Area in square kilometers"
        ),
        "centroid_lat": Column(
            float,
            checks=[
                Check.in_range(TORONTO_LAT_MIN, TORONTO_LAT_MAX, include_min=True, include_max=True)
            ],
            nullable=False,
            description="Centroid latitude (Toronto area)"
        ),
        "centroid_lon": Column(
            float,
            checks=[
                Check.in_range(TORONTO_LON_MIN, TORONTO_LON_MAX, include_min=True, include_max=True)
            ],
            nullable=False,
            description="Centroid longitude (Toronto area)"
        ),
    },
    strict=False,  # Allow additional columns
    coerce=True,   # Try to coerce types
    name="neighbourhoods"
)
