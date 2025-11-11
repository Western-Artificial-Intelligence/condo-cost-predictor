"""Schema for macro table."""
import pandera as pa
from pandera import Column, DataFrameSchema, Check

MacroSchema = DataFrameSchema(
    {
        "month": Column(
            pa.DateTime,
            checks=[
                Check(lambda s: s.dt.year >= 2020, error="Dates before 2020 found"),
                Check(lambda s: s.dt.year <= 2030, error="Dates after 2030 found"),
                Check(lambda s: s.is_unique, error="Duplicate months found")
            ],
            nullable=False,
            description="Month of data (YYYY-MM)"
        ),
        "cpi": Column(
            float,
            checks=[
                Check.greater_than(0),
                Check.less_than(500)  # Reasonable upper bound for CPI index
            ],
            nullable=False,
            description="Consumer Price Index"
        ),
        "mortgage_rate": Column(
            float,
            checks=[
                Check.in_range(0, 20, include_min=True, include_max=True)  # % range
            ],
            nullable=False,
            description="Average mortgage rate (%)"
        ),
        "affordability_index": Column(
            float,
            checks=[
                Check.greater_than(0)
            ],
            nullable=True,  # May be computed later in pipeline
            description="Housing affordability index"
        ),
    },
    strict=False,
    coerce=True,
    name="macro"
)
