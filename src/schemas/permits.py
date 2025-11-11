"""Schema for permits table."""
import pandera as pa
from pandera import Column, DataFrameSchema, Check

PermitsSchema = DataFrameSchema(
    {
        "neighbourhood_id": Column(
            int,
            checks=[Check.greater_than(0)],
            nullable=False,
            description="Foreign key to neighbourhoods.id"
        ),
        "issue_date": Column(
            pa.DateTime,
            checks=[
                Check(lambda s: s.dt.year >= 2020, error="Dates before 2020 found"),
                Check(lambda s: s.dt.year <= 2030, error="Dates after 2030 found"),
            ],
            nullable=False,
            description="Permit issue date"
        ),
        "permit_type": Column(
            str,
            checks=[
                Check.str_length(min_value=1, max_value=50)
            ],
            nullable=False,
            description="Type of permit (e.g., 'residential', 'commercial')"
        ),
        "value": Column(
            float,
            checks=[
                Check.greater_than_or_equal_to(0)
            ],
            nullable=True,  # Some permits may not have value data
            description="Permit value ($CAD)"
        ),
    },
    strict=False,
    coerce=True,
    name="permits"
)
