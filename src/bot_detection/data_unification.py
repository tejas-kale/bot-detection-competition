"""Data unification module for merging and standardising multiple datasets."""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class UnifiedDataset(BaseModel):
    """Metadata for a unified dataset."""
    
    name: str = Field(..., description="Name of the unified dataset")
    source_datasets: List[str] = Field(..., description="Names of source datasets")
    row_count: int = Field(..., description="Total number of rows")
    column_count: int = Field(..., description="Number of columns")
    version: str = Field(..., description="Dataset version")
    created_at: str = Field(..., description="Creation timestamp")


class DataUnifier:
    """Handles merging and standardising multiple datasets."""
    
    def __init__(self):
        self.column_mappings = self._get_column_mappings()
        self.standard_columns = ["id", "prompt_id", "text", "generated", "source"]
    
    def _get_column_mappings(self) -> Dict[str, Dict[str, str]]:
        """Get column mappings for different datasets."""
        return {
            "primary_competition_data": {
                "id": "id",
                "prompt_id": "prompt_id", 
                "text": "text",
                "generated": "generated"
            },
            "daigt_v2_additional_data": {
                "id": "id",
                "prompt_id": "prompt_id",
                "text": "text", 
                "generated": "generated",
                "source": "source"
            }
        }
    
    def standardise_dataset(self, df: pd.DataFrame, dataset_name: str) -> pd.DataFrame:
        """Standardise a dataset to common schema."""
        logger.info(f"Standardising dataset: {dataset_name}")
        
        if dataset_name not in self.column_mappings:
            raise ValueError(f"No column mapping found for dataset: {dataset_name}")
        
        mapping = self.column_mappings[dataset_name]
        standardised_df = pd.DataFrame()
        
        # Map existing columns
        for standard_col, source_col in mapping.items():
            if source_col in df.columns:
                standardised_df[standard_col] = df[source_col]
            else:
                logger.warning(f"Column {source_col} not found in dataset {dataset_name}")
        
        # Add missing standard columns with default values
        for col in self.standard_columns:
            if col not in standardised_df.columns:
                if col == "source":
                    standardised_df[col] = dataset_name
                else:
                    standardised_df[col] = None
        
        # Ensure consistent data types
        standardised_df = self._ensure_data_types(standardised_df)
        
        # Add source information if not present
        if "source" not in standardised_df.columns or standardised_df["source"].isna().all():
            standardised_df["source"] = dataset_name
        
        logger.info(f"Standardised {dataset_name}: {len(standardised_df)} rows, {len(standardised_df.columns)} columns")
        return standardised_df
    
    def _ensure_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Ensure consistent data types across the unified dataset."""
        type_conversions = {
            "id": str,  # Use string to handle different ID formats
            "prompt_id": str,  # Use string to handle different prompt ID formats
            "text": str,
            "generated": int,
            "source": str
        }
        
        for col, target_type in type_conversions.items():
            if col in df.columns:
                try:
                    if target_type == int:
                        # Handle integer conversion more carefully
                        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
                    else:
                        df[col] = df[col].astype(target_type)
                except Exception as e:
                    logger.warning(f"Could not convert column {col} to {target_type}: {e}")
        
        return df
    
    def resolve_id_conflicts(self, datasets: List[Tuple[pd.DataFrame, str]]) -> List[Tuple[pd.DataFrame, str]]:
        """Resolve ID conflicts between datasets by creating unique IDs."""
        logger.info("Resolving ID conflicts between datasets")
        
        resolved_datasets = []
        id_prefix_counter = 1
        
        for df, dataset_name in datasets:
            df_copy = df.copy()
            
            # Create unique IDs by prefixing with dataset identifier
            if "id" in df_copy.columns:
                df_copy["original_id"] = df_copy["id"]
                df_copy["id"] = f"{id_prefix_counter:02d}_" + df_copy["id"].astype(str)
            
            resolved_datasets.append((df_copy, dataset_name))
            id_prefix_counter += 1
        
        return resolved_datasets
    
    def merge_datasets(self, datasets: List[Tuple[pd.DataFrame, str]]) -> pd.DataFrame:
        """Merge multiple standardised datasets into a single unified dataset."""
        logger.info(f"Merging {len(datasets)} datasets")
        
        if not datasets:
            raise ValueError("No datasets provided for merging")
        
        # Standardise all datasets
        standardised_datasets = []
        for df, dataset_name in datasets:
            standardised_df = self.standardise_dataset(df, dataset_name)
            standardised_datasets.append((standardised_df, dataset_name))
        
        # Resolve ID conflicts
        resolved_datasets = self.resolve_id_conflicts(standardised_datasets)
        
        # Concatenate all datasets
        unified_dfs = [df for df, _ in resolved_datasets]
        unified_df = pd.concat(unified_dfs, ignore_index=True)
        
        # Remove duplicates based on text content (keep first occurrence)
        logger.info("Removing duplicate text entries")
        initial_count = len(unified_df)
        unified_df = unified_df.drop_duplicates(subset=["text"], keep="first")
        duplicates_removed = initial_count - len(unified_df)
        
        if duplicates_removed > 0:
            logger.info(f"Removed {duplicates_removed} duplicate text entries")
        
        # Reorder columns
        column_order = [col for col in self.standard_columns if col in unified_df.columns]
        other_columns = [col for col in unified_df.columns if col not in column_order]
        unified_df = unified_df[column_order + other_columns]
        
        logger.info(f"Created unified dataset: {len(unified_df)} rows, {len(unified_df.columns)} columns")
        return unified_df
    
    def load_datasets_from_directory(self, directory: Path) -> List[Tuple[pd.DataFrame, str]]:
        """Load datasets from a directory structure."""
        datasets = []
        
        # Look for CSV files in subdirectories
        for subdir in directory.iterdir():
            if subdir.is_dir():
                dataset_name = subdir.name
                
                # Find the main data file
                main_files = []
                for pattern in ["train_essay*.csv", "*train*.csv", "*.csv"]:
                    main_files.extend(list(subdir.glob(pattern)))
                
                if main_files:
                    # Use the first suitable file found
                    main_file = main_files[0]
                    
                    try:
                        logger.info(f"Loading dataset from {main_file}")
                        df = pd.read_csv(main_file)
                        datasets.append((df, dataset_name))
                        
                    except Exception as e:
                        logger.error(f"Error loading dataset from {main_file}: {e}")
                else:
                    logger.warning(f"No CSV files found in {subdir}")
        
        return datasets
    
    def save_unified_dataset(self, df: pd.DataFrame, output_path: Path, format: str = "parquet") -> Path:
        """Save the unified dataset to file."""
        logger.info(f"Saving unified dataset to {output_path} in {format} format")
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format.lower() == "parquet":
            if not str(output_path).endswith(".parquet"):
                output_path = output_path.with_suffix(".parquet")
            df.to_parquet(output_path, index=False)
        elif format.lower() == "csv":
            if not str(output_path).endswith(".csv"):
                output_path = output_path.with_suffix(".csv")
            df.to_csv(output_path, index=False)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        logger.info(f"Saved unified dataset: {output_path} ({len(df)} rows)")
        return output_path
    
    def create_unified_dataset_metadata(self, df: pd.DataFrame, source_datasets: List[str], 
                                      version: str) -> UnifiedDataset:
        """Create metadata for the unified dataset."""
        from datetime import datetime
        
        return UnifiedDataset(
            name="unified_bot_detection_dataset",
            source_datasets=source_datasets,
            row_count=len(df),
            column_count=len(df.columns),
            version=version,
            created_at=datetime.now().isoformat()
        )