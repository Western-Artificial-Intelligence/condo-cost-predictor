"""Schema for the joined dataset (tor_neighborhood_condorental.parquet)."""
import pandera as pa
from pandera import Column, DataFrameSchema, Check

# helper function to generate crime column schemas
def create_crime_columns():
    """schema for all crime-related columns matching actual data."""
    years = range(2014, 2025)  # 2014-2024
    crime_cols = {}
    
    # ASSAULT: has both counts and rates
    for year in years:
        crime_cols[f"ASSAULT_{year}"] = Column(
            float, checks=[Check.greater_than_or_equal_to(0)], nullable=True, coerce=True
        )
        crime_cols[f"ASSAULT_RATE_{year}"] = Column(
            float, checks=[Check.greater_than_or_equal_to(0)], nullable=True, coerce=True
        )
    
    # AUTOTHEFT: has counts and rates (plus duplicates)
    for year in years:
        crime_cols[f"AUTOTHEFT_{year}"] = Column(
            float, checks=[Check.greater_than_or_equal_to(0)], nullable=True, coerce=True
        )
        crime_cols[f"AUTOTHEFT_RATE_{year}"] = Column(
            float, checks=[Check.greater_than_or_equal_to(0)], nullable=True, coerce=True
        )
    
    # AUTOTHEFT duplicates (data quality issues)
    crime_cols["AUTOTHEFT_2014_1"] = Column(float, nullable=True, coerce=True)
    for i in range(1, 10):
        crime_cols[f"AUTOTHEFT_2015_{i}"] = Column(float, nullable=True, coerce=True)
    
    # BIKETHEFT: ONLY RATES (no counts in actual data!)
    for year in years:
        crime_cols[f"BIKETHEFT_RATE_{year}"] = Column(
            float, checks=[Check.greater_than_or_equal_to(0)], nullable=True, coerce=True
        )
        # BIKETHEFT_RATE duplicates
        crime_cols[f"BIKETHEFT_RATE_{year}_1"] = Column(float, nullable=True, coerce=True)
    
    # BREAKENTER: ONLY COUNTS (no rates in actual data!)
    for year in years:
        crime_cols[f"BREAKENTER_{year}"] = Column(
            float, checks=[Check.greater_than_or_equal_to(0)], nullable=True, coerce=True
        )
    
    # HOMICIDE, ROBBERY, SHOOTING, THEFTFROMMV, THEFTOVER: have both counts and rates
    for crime_type in ["HOMICIDE", "ROBBERY", "SHOOTING", "THEFTFROMMV", "THEFTOVER"]:
        for year in years:
            crime_cols[f"{crime_type}_{year}"] = Column(
                float, checks=[Check.greater_than_or_equal_to(0)], nullable=True, coerce=True
            )
            crime_cols[f"{crime_type}_RATE_{year}"] = Column(
                float, checks=[Check.greater_than_or_equal_to(0)], nullable=True, coerce=True
            )
    
    return crime_cols


TorontoCondoDataSchema = DataFrameSchema(
    {
        # === Neighborhood Identifiers ===
        "_id": Column(int, nullable=True, coerce=True, description="MongoDB-style ID"),
        "AREA_ID": Column(int, nullable=True, coerce=True, description="Area ID"),
        "AREA_ATTR_ID": Column(int, nullable=True, coerce=True, description="Area attribute ID"),
        "PARENT_AREA_ID": Column(object, nullable=True, description="Parent area ID (mostly NULL)"),
        "AREA_SHORT_CODE": Column(str, nullable=True, description="Short area code"),
        "AREA_LONG_CODE": Column(str, nullable=True, description="Long area code"),
        "AREA_NAME": Column(
            str,
            checks=[Check.str_length(min_value=1, max_value=200)],
            nullable=False,
            description="Neighborhood name"
        ),
        "AREA_NAME_1": Column(str, nullable=True, description="Duplicate area name from crime join"),
        "AREA_DESC": Column(str, nullable=True, description="Area description"),
        "CLASSIFICATION": Column(str, nullable=True, description="Neighborhood classification"),
        "CLASSIFICATION_CODE": Column(str, nullable=True, description="Classification code"),
        "OBJECTID": Column(int, nullable=True, coerce=True, description="GIS object ID"),
        
        # === Geometry ===
        "geometry_wkt": Column(str, nullable=True, description="Neighborhood boundary (WKT)"),
        "geometry_type": Column(str, nullable=True, description="Geometry type (e.g., Polygon)"),
        "geometry_wkt_1": Column(str, nullable=True, description="Duplicate geometry from transit join"),
        "geometry_type_1": Column(str, nullable=True, description="Duplicate geometry type"),
        
        # === Region Classification (for TREB target variables) ===
        "Region_classif": Column(
            str,
            nullable=True,
            description="TREB region classification (e.g., Toronto C10)"
        ),
        "Area": Column(str, nullable=True, description="Area label"),
        
        # === Target Variables (Rental Market) ===
        "Bachelor Leased": Column(
            float,
            checks=[Check.greater_than_or_equal_to(0)],
            nullable=True,
            coerce=True,
            description="Number of bachelor units leased"
        ),
        "bachelor_avg_lease_rate": Column(
            float,
            checks=[Check.greater_than_or_equal_to(0)],
            nullable=True,
            coerce=True,
            description="Average bachelor lease rate ($CAD)"
        ),
        "1_bedrooms_leased": Column(
            float,
            checks=[Check.greater_than_or_equal_to(0)],
            nullable=True,
            coerce=True,
            description="Number of 1-bedroom units leased"
        ),
        "1_bed_room_avg_lease_rate": Column(
            float,
            checks=[Check.greater_than_or_equal_to(0)],
            nullable=True,
            coerce=True,
            description="Average 1-bedroom lease rate ($CAD)"
        ),
        "2_bedrooms_leased": Column(
            float,
            checks=[Check.greater_than_or_equal_to(0)],
            nullable=True,
            coerce=True,
            description="Number of 2-bedroom units leased"
        ),
        "2_bedrooms_avg_lease_rate": Column(
            float,
            checks=[Check.greater_than_or_equal_to(0)],
            nullable=True,
            coerce=True,
            description="Average 2-bedroom lease rate ($CAD)"
        ),
        "3_bedrooms_leased": Column(
            float,
            checks=[Check.greater_than_or_equal_to(0)],
            nullable=True,
            coerce=True,
            description="Number of 3-bedroom units leased"
        ),
        "3_bedrooms_avg_lease_rate": Column(
            float,
            checks=[Check.greater_than_or_equal_to(0)],
            nullable=True,
            coerce=True,
            description="Average 3-bedroom lease rate ($CAD)"
        ),
        
        # === Spatial Features ===
        "area_sq_meters": Column(
            float,
            checks=[
                Check.greater_than(0),
                Check.less_than(100_000_000)  
            ],
            nullable=True,
            coerce=True,
            description="Neighborhood area (m²)"
        ),
        "perimeter_meters": Column(
            float,
            checks=[Check.greater_than(0)],
            nullable=True,
            coerce=True,
            description="Neighborhood perimeter (m)"
        ),
        
        # === Parks ===
        "park_count": Column(
            int,
            checks=[Check.greater_than_or_equal_to(0)],
            nullable=True,
            coerce=True,
            description="Number of parks in neighborhood"
        ),
        
        # === Crime Data (generated dynamically) ===
        **create_crime_columns(),
        
        # === Population ===
        "POPULATION_2024": Column(
            float,
            checks=[Check.greater_than_or_equal_to(0)],
            nullable=True,
            coerce=True,
            description="Population in 2024"
        ),
        
        # === Transit Features ===
        "total_stop_count": Column(
            int,
            checks=[Check.greater_than_or_equal_to(0)],
            nullable=True,
            coerce=True,
            description="Total transit stops in neighborhood"
        ),
        "avg_stop_frequency": Column(
            float,
            checks=[Check.greater_than_or_equal_to(0)],
            nullable=True,
            coerce=True,
            description="Average stop frequency (stops per day)"
        ),
        "max_stop_frequency": Column(
            float,
            checks=[Check.greater_than_or_equal_to(0)],
            nullable=True,
            coerce=True,
            description="Max stop frequency (stops per day)"
        ),
        "total_line_length_meters": Column(
            float,
            checks=[Check.greater_than_or_equal_to(0)],
            nullable=True,
            coerce=True,
            description="Total transit line length (m)"
        ),
        "transit_line_density": Column(
            float,
            checks=[Check.greater_than_or_equal_to(0)],
            nullable=True,
            coerce=True,
            description="Transit line density (m per m²)"
        ),
        "distinct_route_count": Column(
            int,
            checks=[Check.greater_than_or_equal_to(0)],
            nullable=True,
            coerce=True,
            description="Number of distinct transit routes"
        ),
    },
    strict=False,  # Allow additional columns
    coerce=True,   # Try to coerce types
    name="toronto_condo_rental_data"
)
