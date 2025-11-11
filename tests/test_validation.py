"""Unit tests for data validation schemas."""
import pandas as pd
import pytest
from pandera.errors import SchemaError

from src.schemas import (
    NeighbourhoodsSchema,
    SocioeconomicsSchema,
    HousingIndicatorsSchema,
    TransitSchema,
    MacroSchema,
)


class TestNeighbourhoodsSchema:
    """Tests for neighbourhoods schema."""
    
    def test_valid_data(self):
        """Test that valid data passes."""
        df = pd.DataFrame({
            "id": [1, 2, 3],
            "name": ["Downtown", "Midtown", "Uptown"],
            "geometry": ["POLYGON(...)", "POLYGON(...)", "POLYGON(...)"],
            "area_km2": [5.2, 8.1, 12.3],
            "centroid_lat": [43.65, 43.70, 43.75],
            "centroid_lon": [-79.38, -79.40, -79.42],
        })
        # Should not raise
        NeighbourhoodsSchema.validate(df)
    
    def test_duplicate_ids(self):
        """Test that duplicate IDs are caught."""
        df = pd.DataFrame({
            "id": [1, 1, 2],  # Duplicate
            "name": ["Downtown", "Downtown2", "Midtown"],
            "geometry": [None, None, None],
            "area_km2": [5.2, 8.1, 12.3],
            "centroid_lat": [43.65, 43.70, 43.75],
            "centroid_lon": [-79.38, -79.40, -79.42],
        })
        with pytest.raises(SchemaError):
            NeighbourhoodsSchema.validate(df)
    
    def test_invalid_coordinates(self):
        """Test that out-of-range coordinates are caught."""
        df = pd.DataFrame({
            "id": [1],
            "name": ["Downtown"],
            "geometry": [None],
            "area_km2": [5.2],
            "centroid_lat": [45.0],  # Outside Toronto range
            "centroid_lon": [-79.38],
        })
        with pytest.raises(SchemaError):
            NeighbourhoodsSchema.validate(df)


class TestHousingIndicatorsSchema:
    """Tests for housing_indicators schema."""
    
    def test_valid_data(self):
        """Test that valid data passes."""
        df = pd.DataFrame({
            "neighbourhood_id": [1, 1, 2],
            "month": pd.to_datetime(["2023-01-01", "2023-02-01", "2023-01-01"]),
            "starts": [10, 15, 8],
            "completions": [5, 7, 3],
            "stock": [1000, 1005, 800],
        })
        HousingIndicatorsSchema.validate(df)
    
    def test_negative_values(self):
        """Test that negative values are caught."""
        df = pd.DataFrame({
            "neighbourhood_id": [1],
            "month": pd.to_datetime(["2023-01-01"]),
            "starts": [-5],  # Invalid
            "completions": [5],
            "stock": [1000],
        })
        with pytest.raises(SchemaError):
            HousingIndicatorsSchema.validate(df)


class TestTransitSchema:
    """Tests for transit schema."""
    
    def test_valid_data(self):
        """Test that valid data passes."""
        df = pd.DataFrame({
            "stop_id": ["1001", "1002"],
            "stop_name": ["Union Station", "King Station"],
            "stop_lat": [43.645, 43.649],
            "stop_lon": [-79.380, -79.376],
        })
        TransitSchema.validate(df)
    
    def test_duplicate_stops(self):
        """Test that duplicate stop IDs are caught."""
        df = pd.DataFrame({
            "stop_id": ["1001", "1001"],  # Duplicate
            "stop_name": ["Union Station", "Union Station 2"],
            "stop_lat": [43.645, 43.649],
            "stop_lon": [-79.380, -79.376],
        })
        with pytest.raises(SchemaError):
            TransitSchema.validate(df)


class TestMacroSchema:
    """Tests for macro schema."""
    
    def test_valid_data(self):
        """Test that valid data passes."""
        df = pd.DataFrame({
            "month": pd.to_datetime(["2023-01-01", "2023-02-01", "2023-03-01"]),
            "cpi": [150.2, 151.0, 151.5],
            "mortgage_rate": [5.5, 5.6, 5.7],
            "affordability_index": [120.0, 119.5, 119.0],
        })
        MacroSchema.validate(df)
    
    def test_duplicate_months(self):
        """Test that duplicate months are caught."""
        df = pd.DataFrame({
            "month": pd.to_datetime(["2023-01-01", "2023-01-01"]),  # Duplicate
            "cpi": [150.2, 151.0],
            "mortgage_rate": [5.5, 5.6],
            "affordability_index": [120.0, 119.5],
        })
        with pytest.raises(SchemaError):
            MacroSchema.validate(df)
