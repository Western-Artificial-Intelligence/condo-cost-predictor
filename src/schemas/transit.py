"""Schema for transit table."""
import pandera as pa
from pandera import Column, DataFrameSchema, Check

# Toronto bounding box
TORONTO_LAT_MIN = 43.58
TORONTO_LAT_MAX = 43.86
TORONTO_LON_MIN = -79.64
TORONTO_LON_MAX = -79.12

TransitSchema = DataFrameSchema(
    {
        "stop_id": Column(
            str,
            checks=[
                Check(lambda s: s.is_unique, error="Duplicate stop IDs found")
            ],
            nullable=False,
            description="Unique transit stop identifier"
        ),
        "stop_name": Column(
            str,
            checks=[
                Check.str_length(min_value=1, max_value=200)
            ],
            nullable=False,
            description="Transit stop name"
        ),
        "stop_lat": Column(
            float,
            checks=[
                Check.in_range(TORONTO_LAT_MIN, TORONTO_LAT_MAX, include_min=True, include_max=True)
            ],
            nullable=False,
            description="Stop latitude (Toronto area)"
        ),
        "stop_lon": Column(
            float,
            checks=[
                Check.in_range(TORONTO_LON_MIN, TORONTO_LON_MAX, include_min=True, include_max=True)
            ],
            nullable=False,
            description="Stop longitude (Toronto area)"
        ),
    },
    strict=False,
    coerce=True,
    name="transit"
)
