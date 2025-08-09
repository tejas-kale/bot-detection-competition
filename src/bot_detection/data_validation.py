"""Data validation module for ensuring data quality and schema compliance."""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Union

import pandas as pd
from pydantic import BaseModel, Field, ValidationError

logger = logging.getLogger(__name__)


class ColumnSchema(BaseModel):
    """Schema definition for a dataset column."""
    
    name: str = Field(..., description="Column name")
    dtype: str = Field(..., description="Expected data type")
    nullable: bool = Field(default=True, description="Whether nulls are allowed")
    unique: bool = Field(default=False, description="Whether values must be unique")
    min_length: Optional[int] = Field(None, description="Minimum string length")
    max_length: Optional[int] = Field(None, description="Maximum string length")
    allowed_values: Optional[Set[Union[str, int, float]]] = Field(None, description="Set of allowed values")


class DatasetSchema(BaseModel):
    """Schema definition for a complete dataset."""
    
    name: str = Field(..., description="Dataset name")
    columns: List[ColumnSchema] = Field(..., description="Column schemas")
    min_rows: int = Field(default=1, description="Minimum number of rows")
    max_rows: Optional[int] = Field(None, description="Maximum number of rows")
    
    def get_column_names(self) -> Set[str]:
        """Get set of expected column names."""
        return {col.name for col in self.columns}
    
    def get_column_schema(self, column_name: str) -> Optional[ColumnSchema]:
        """Get schema for a specific column."""
        for col in self.columns:
            if col.name == column_name:
                return col
        return None


class ValidationResult(BaseModel):
    """Result of data validation."""
    
    dataset_name: str
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    row_count: int
    column_count: int


class DataValidator:
    """Data validation and schema checking."""
    
    def __init__(self):
        self.schemas = self._get_expected_schemas()
    
    def _get_expected_schemas(self) -> Dict[str, DatasetSchema]:
        """Get expected schemas for known datasets."""
        return {
            "primary_competition_data": DatasetSchema(
                name="primary_competition_data",
                columns=[
                    ColumnSchema(name="id", dtype="int64", nullable=False, unique=True),
                    ColumnSchema(name="prompt_id", dtype="int64", nullable=False),
                    ColumnSchema(name="text", dtype="object", nullable=False, min_length=10),
                    ColumnSchema(name="generated", dtype="int64", nullable=False, allowed_values={0, 1})
                ],
                min_rows=1000
            ),
            "daigt_v2_additional_data": DatasetSchema(
                name="daigt_v2_additional_data",
                columns=[
                    ColumnSchema(name="id", dtype="object", nullable=False, unique=True),
                    ColumnSchema(name="prompt_id", dtype="object", nullable=False),
                    ColumnSchema(name="text", dtype="object", nullable=False, min_length=10),
                    ColumnSchema(name="generated", dtype="int64", nullable=False, allowed_values={0, 1}),
                    ColumnSchema(name="source", dtype="object", nullable=True)
                ],
                min_rows=100
            ),
            "train_prompts": DatasetSchema(
                name="train_prompts",
                columns=[
                    ColumnSchema(name="prompt_id", dtype="int64", nullable=False, unique=True),
                    ColumnSchema(name="prompt_name", dtype="object", nullable=False),
                    ColumnSchema(name="instructions", dtype="object", nullable=False, min_length=10),
                    ColumnSchema(name="source_text", dtype="object", nullable=False, min_length=10)
                ],
                min_rows=1
            )
        }
    
    def validate_dataframe(self, df: pd.DataFrame, schema: DatasetSchema) -> ValidationResult:
        """Validate a DataFrame against a schema."""
        result = ValidationResult(
            dataset_name=schema.name,
            is_valid=True,
            row_count=len(df),
            column_count=len(df.columns)
        )
        
        # Check row count
        if len(df) < schema.min_rows:
            result.errors.append(f"Insufficient rows: {len(df)} < {schema.min_rows}")
            result.is_valid = False
        
        if schema.max_rows and len(df) > schema.max_rows:
            result.errors.append(f"Too many rows: {len(df)} > {schema.max_rows}")
            result.is_valid = False
        
        # Check columns exist
        expected_columns = schema.get_column_names()
        actual_columns = set(df.columns)
        
        missing_columns = expected_columns - actual_columns
        if missing_columns:
            result.errors.append(f"Missing columns: {missing_columns}")
            result.is_valid = False
        
        extra_columns = actual_columns - expected_columns
        if extra_columns:
            result.warnings.append(f"Extra columns found: {extra_columns}")
        
        # Validate each column
        for column_name in expected_columns.intersection(actual_columns):
            column_schema = schema.get_column_schema(column_name)
            if column_schema:
                column_errors = self._validate_column(df[column_name], column_schema)
                result.errors.extend(column_errors)
                if column_errors:
                    result.is_valid = False
        
        return result
    
    def _validate_column(self, series: pd.Series, schema: ColumnSchema) -> List[str]:
        """Validate a single column against its schema."""
        errors = []
        
        # Check nulls
        if not schema.nullable and series.isnull().any():
            null_count = series.isnull().sum()
            errors.append(f"Column '{schema.name}' has {null_count} null values but nulls not allowed")
        
        # Check uniqueness
        if schema.unique and not series.is_unique:
            duplicate_count = len(series) - len(series.unique())
            errors.append(f"Column '{schema.name}' has {duplicate_count} duplicate values but must be unique")
        
        # Check data type (basic check)
        try:
            if schema.dtype == "int64" and not pd.api.types.is_integer_dtype(series):
                errors.append(f"Column '{schema.name}' expected int64 but got {series.dtype}")
            elif schema.dtype == "object" and not pd.api.types.is_object_dtype(series):
                errors.append(f"Column '{schema.name}' expected object but got {series.dtype}")
        except Exception as e:
            logger.warning(f"Could not check dtype for column {schema.name}: {e}")
        
        # Check string lengths
        if schema.dtype == "object" and (schema.min_length or schema.max_length):
            non_null_series = series.dropna()
            if len(non_null_series) > 0:
                str_lengths = non_null_series.astype(str).str.len()
                
                if schema.min_length:
                    short_count = (str_lengths < schema.min_length).sum()
                    if short_count > 0:
                        errors.append(f"Column '{schema.name}' has {short_count} values shorter than {schema.min_length}")
                
                if schema.max_length:
                    long_count = (str_lengths > schema.max_length).sum()
                    if long_count > 0:
                        errors.append(f"Column '{schema.name}' has {long_count} values longer than {schema.max_length}")
        
        # Check allowed values
        if schema.allowed_values:
            non_null_series = series.dropna()
            invalid_values = set(non_null_series.unique()) - schema.allowed_values
            if invalid_values:
                errors.append(f"Column '{schema.name}' has invalid values: {invalid_values}")
        
        return errors
    
    def validate_file(self, file_path: Path, dataset_name: Optional[str] = None) -> ValidationResult:
        """Validate a CSV/Parquet file against expected schema."""
        if not file_path.exists():
            return ValidationResult(
                dataset_name=dataset_name or file_path.stem,
                is_valid=False,
                errors=[f"File does not exist: {file_path}"],
                row_count=0,
                column_count=0
            )
        
        try:
            # Load the file
            if file_path.suffix.lower() == '.csv':
                df = pd.read_csv(file_path)
            elif file_path.suffix.lower() in ['.parquet', '.pq']:
                df = pd.read_parquet(file_path)
            else:
                return ValidationResult(
                    dataset_name=dataset_name or file_path.stem,
                    is_valid=False,
                    errors=[f"Unsupported file format: {file_path.suffix}"],
                    row_count=0,
                    column_count=0
                )
            
            # Determine schema
            if dataset_name and dataset_name in self.schemas:
                schema = self.schemas[dataset_name]
            else:
                # Try to infer from filename
                inferred_name = self._infer_dataset_name(file_path.stem)
                if inferred_name and inferred_name in self.schemas:
                    schema = self.schemas[inferred_name]
                else:
                    return ValidationResult(
                        dataset_name=dataset_name or file_path.stem,
                        is_valid=False,
                        errors=[f"No schema found for dataset: {dataset_name or file_path.stem}"],
                        row_count=len(df),
                        column_count=len(df.columns)
                    )
            
            return self.validate_dataframe(df, schema)
            
        except Exception as e:
            return ValidationResult(
                dataset_name=dataset_name or file_path.stem,
                is_valid=False,
                errors=[f"Error loading file: {e}"],
                row_count=0,
                column_count=0
            )
    
    def _infer_dataset_name(self, filename: str) -> Optional[str]:
        """Infer dataset name from filename."""
        filename_lower = filename.lower()
        
        if "train_essay" in filename_lower or "train_" in filename_lower:
            if "prompt" in filename_lower:
                return "train_prompts"
            return "primary_competition_data"
        elif "daigt" in filename_lower:
            return "daigt_v2_additional_data"
        
        return None
    
    def validate_directory(self, directory: Path) -> Dict[str, ValidationResult]:
        """Validate all CSV/Parquet files in a directory."""
        results = {}
        
        for file_path in directory.glob("*.csv"):
            result = self.validate_file(file_path)
            results[file_path.name] = result
        
        for file_path in directory.glob("*.parquet"):
            result = self.validate_file(file_path)
            results[file_path.name] = result
        
        return results