"""Schema for crime table."""
import pandera as pa
from pandera import Column, DataFrameSchema, Check

CrimeSchema = DataFrameSchema(
    {
        "neighbourhood_id": Column(
            int,
            checks=[Check.greater_than(0)],
            nullable=False,
            description="Foreign key to neighbourhoods.id"
        ),
        "year": Column(
            int,
            checks=[
                Check.in_range(2020, 2030, include_min=True, include_max=True)
            ],
            nullable=False,
            description="Year of data"
        ),
        "crime_type": Column(
            str,
            checks=[
                Check.str_length(min_value=1, max_value=100)
            ],
            nullable=False,
            description="Type of crime"
        ),
        "incidents_per_100k": Column(
            float,
            checks=[
                Check.greater_than_or_equal_to(0)
            ],
            nullable=False,
            description="Crime incidents per 100k population"
        ),
    },
    strict=False,
    coerce=True,
    name="crime"
)
