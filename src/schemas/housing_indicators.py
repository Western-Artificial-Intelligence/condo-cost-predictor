"""Schema for housing_indicators table."""
import pandera as pa
from pandera import Column, DataFrameSchema, Check

HousingIndicatorsSchema = DataFrameSchema(
    {
        "neighbourhood_id": Column(
            int,
            checks=[Check.greater_than(0)],
            nullable=False,
            description="Foreign key to neighbourhoods.id"
        ),
        "month": Column(
            pa.DateTime,
            checks=[
                Check(lambda s: s.dt.year >= 2020, error="Dates before 2020 found"),
                Check(lambda s: s.dt.year <= 2030, error="Dates after 2030 found"),
            ],
            nullable=False,
            description="Month of data (YYYY-MM format)"
        ),
        "starts": Column(
            int,
            checks=[
                Check.greater_than_or_equal_to(0)
            ],
            nullable=True,  # May be missing for some months
            description="Number of housing starts"
        ),
        "completions": Column(
            int,
            checks=[
                Check.greater_than_or_equal_to(0)
            ],
            nullable=True,
            description="Number of completions"
        ),
        "stock": Column(
            int,
            checks=[
                Check.greater_than_or_equal_to(0)
            ],
            nullable=True,
            description="Total housing stock"
        ),
    },
    strict=False,
    coerce=True,
    name="housing_indicators"
)
