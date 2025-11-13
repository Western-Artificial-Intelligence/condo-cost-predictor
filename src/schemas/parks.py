"""Schema for parks table."""
import pandera as pa
from pandera import Column, DataFrameSchema, Check

ParksSchema = DataFrameSchema(
    {
        "neighbourhood_id": Column(
            int,
            checks=[Check.greater_than(0)],
            nullable=False,
            description="Foreign key to neighbourhoods.id"
        ),
        "count_parks": Column(
            int,
            checks=[
                Check.greater_than_or_equal_to(0)
            ],
            nullable=False,
            description="Number of parks in neighbourhood"
        ),
        "area_green_space": Column(
            float,
            checks=[
                Check.greater_than_or_equal_to(0)
            ],
            nullable=True,  # May be missing for some neighbourhoods
            description="Total green space area (km²)"
        ),
    },
    strict=False,
    coerce=True,
    name="parks"
)
