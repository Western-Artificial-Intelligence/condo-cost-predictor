"""Schema for socioeconomics table."""
import pandera as pa
from pandera import Column, DataFrameSchema, Check

SocioeconomicsSchema = DataFrameSchema(
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
        "median_income": Column(
            float,
            checks=[
                Check.greater_than(0),
                Check.less_than(500000)  # Reasonable upper bound for Toronto
            ],
            nullable=True,  # May be missing for some years/neighbourhoods
            description="Median household income ($CAD)"
        ),
        "renters_pct": Column(
            float,
            checks=[
                Check.in_range(0, 100, include_min=True, include_max=True)
            ],
            nullable=True,
            description="Percentage of renters (0-100)"
        ),
        "population_density": Column(
            float,
            checks=[Check.greater_than_or_equal_to(0)],
            nullable=True,
            description="People per km²"
        ),
        "immigrants_pct": Column(
            float,
            checks=[
                Check.in_range(0, 100, include_min=True, include_max=True)
            ],
            nullable=True,
            description="Percentage of immigrants (0-100)"
        ),
        "education_pct": Column(
            float,
            checks=[
                Check.in_range(0, 100, include_min=True, include_max=True)
            ],
            nullable=True,
            description="Percentage with post-secondary education (0-100)"
        ),
        "unemployment_rate": Column(
            float,
            checks=[
                Check.in_range(0, 100, include_min=True, include_max=True)
            ],
            nullable=True,
            description="Unemployment rate (0-100)"
        ),
    },
    strict=False,
    coerce=True,
    name="socioeconomics"
)
