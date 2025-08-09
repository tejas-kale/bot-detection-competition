"""Prefect flows for orchestrating the data ingestion pipeline."""

import logging
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
from prefect import flow, task
from prefect.logging import get_run_logger

from .config import Settings, get_settings, setup_gcp_credentials
from .data_ingestion import DataIngestionPipeline, DatasetInfo
from .data_unification import DataUnifier
from .data_validation import DataValidator, ValidationResult
from .gcs_storage import GCSStorageManager


@task(name="setup_environment")
def setup_environment_task(environment: str = "dev") -> Settings:
    """Set up environment configuration and credentials."""
    logger = get_run_logger()
    logger.info(f"Setting up environment: {environment}")
    
    settings = get_settings(environment)
    setup_gcp_credentials(settings)
    
    return settings


@task(name="download_datasets")
def download_datasets_task(settings: Settings) -> Dict[str, List[Path]]:
    """Download all required datasets from Kaggle."""
    logger = get_run_logger()
    
    pipeline = DataIngestionPipeline(settings)
    datasets = pipeline.get_competition_datasets()
    
    logger.info(f"Starting download of {len(datasets)} datasets")
    downloaded_data = pipeline.download_datasets(datasets)
    
    # Log download results
    total_files = sum(len(files) for files in downloaded_data.values())
    logger.info(f"Downloaded {total_files} files across {len(downloaded_data)} datasets")
    
    return downloaded_data


@task(name="validate_datasets")
def validate_datasets_task(downloaded_data: Dict[str, List[Path]]) -> Dict[str, List[ValidationResult]]:
    """Validate all downloaded datasets."""
    logger = get_run_logger()
    
    validator = DataValidator()
    validation_results = {}
    
    for dataset_name, files in downloaded_data.items():
        logger.info(f"Validating dataset: {dataset_name}")
        dataset_results = []
        
        for file_path in files:
            if file_path.suffix.lower() in ['.csv', '.parquet']:
                result = validator.validate_file(file_path, dataset_name)
                dataset_results.append(result)
                
                if result.is_valid:
                    logger.info(f"✓ {file_path.name}: Valid ({result.row_count} rows)")
                else:
                    logger.warning(f"✗ {file_path.name}: Invalid - {len(result.errors)} errors")
                    for error in result.errors:
                        logger.warning(f"  - {error}")
        
        validation_results[dataset_name] = dataset_results
    
    return validation_results


@task(name="unify_datasets")
def unify_datasets_task(
    downloaded_data: Dict[str, List[Path]], 
    validation_results: Dict[str, List[ValidationResult]],
    settings: Settings
) -> Path:
    """Unify all valid datasets into a single dataset."""
    logger = get_run_logger()
    
    unifier = DataUnifier()
    datasets_to_merge = []
    
    # Load valid datasets
    for dataset_name, files in downloaded_data.items():
        # Check if dataset passed validation
        valid_files = []
        if dataset_name in validation_results:
            for i, result in enumerate(validation_results[dataset_name]):
                if result.is_valid and i < len(files):
                    valid_files.append(files[i])
        
        # Load the main CSV file from each dataset
        for file_path in valid_files:
            if file_path.suffix.lower() == '.csv' and 'train' in file_path.name.lower():
                try:
                    logger.info(f"Loading dataset for unification: {file_path}")
                    df = pd.read_csv(file_path)
                    datasets_to_merge.append((df, dataset_name))
                except Exception as e:
                    logger.error(f"Error loading {file_path}: {e}")
    
    if not datasets_to_merge:
        raise ValueError("No valid datasets found for unification")
    
    # Merge datasets
    logger.info(f"Merging {len(datasets_to_merge)} datasets")
    unified_df = unifier.merge_datasets(datasets_to_merge)
    
    # Save unified dataset
    project_root = Path(__file__).parent.parent.parent
    version = DataIngestionPipeline(settings).create_data_version()
    output_path = project_root / "data" / "processed" / f"unified_dataset_{version}"
    
    final_path = unifier.save_unified_dataset(unified_df, output_path, format="parquet")
    logger.info(f"Unified dataset saved: {final_path}")
    
    return final_path


@task(name="upload_to_gcs")
def upload_to_gcs_task(local_path: Path, settings: Settings) -> str:
    """Upload the unified dataset to Google Cloud Storage."""
    logger = get_run_logger()
    
    storage_manager = GCSStorageManager(settings)
    
    # Create GCS path with versioning
    pipeline = DataIngestionPipeline(settings)
    version = pipeline.create_data_version()
    gcs_path = f"datasets/unified/{version}/{local_path.name}"
    
    gcs_url = storage_manager.upload_file(local_path, gcs_path)
    logger.info(f"Uploaded to GCS: {gcs_url}")
    
    return gcs_url


@task(name="create_metadata")
def create_metadata_task(
    unified_path: Path, 
    downloaded_data: Dict[str, List[Path]], 
    settings: Settings
) -> Path:
    """Create and save metadata for the unified dataset."""
    logger = get_run_logger()
    
    # Load unified dataset to get stats
    df = pd.read_parquet(unified_path)
    
    # Create metadata
    unifier = DataUnifier()
    pipeline = DataIngestionPipeline(settings)
    version = pipeline.create_data_version()
    source_datasets = list(downloaded_data.keys())
    
    metadata = unifier.create_unified_dataset_metadata(df, source_datasets, version)
    
    # Save metadata
    metadata_path = unified_path.with_suffix('.json')
    with open(metadata_path, 'w') as f:
        f.write(metadata.model_dump_json(indent=2))
    
    logger.info(f"Metadata saved: {metadata_path}")
    return metadata_path


@flow(name="data_ingestion_pipeline")
def data_ingestion_pipeline(environment: str = "dev") -> Dict[str, str]:
    """Main data ingestion and unification pipeline."""
    logger = get_run_logger()
    logger.info("Starting data ingestion pipeline")
    
    # Set up environment
    settings = setup_environment_task(environment)
    
    # Download datasets
    downloaded_data = download_datasets_task(settings)
    
    # Validate datasets
    validation_results = validate_datasets_task(downloaded_data)
    
    # Check if any datasets are valid
    valid_datasets = []
    for dataset_name, results in validation_results.items():
        if any(result.is_valid for result in results):
            valid_datasets.append(dataset_name)
    
    if not valid_datasets:
        raise ValueError("No valid datasets found after validation")
    
    logger.info(f"Found {len(valid_datasets)} valid datasets: {valid_datasets}")
    
    # Unify datasets
    unified_path = unify_datasets_task(downloaded_data, validation_results, settings)
    
    # Upload to GCS
    gcs_url = upload_to_gcs_task(unified_path, settings)
    
    # Create metadata
    metadata_path = create_metadata_task(unified_path, downloaded_data, settings)
    
    logger.info("Data ingestion pipeline completed successfully")
    
    return {
        "unified_dataset_path": str(unified_path),
        "gcs_url": gcs_url,
        "metadata_path": str(metadata_path),
        "environment": environment
    }


@flow(name="validate_existing_data")
def validate_existing_data_flow(data_directory: Optional[str] = None) -> Dict[str, ValidationResult]:
    """Flow to validate existing data files."""
    logger = get_run_logger()
    
    if data_directory:
        data_dir = Path(data_directory)
    else:
        project_root = Path(__file__).parent.parent.parent
        data_dir = project_root / "data" / "raw"
    
    logger.info(f"Validating data in: {data_dir}")
    
    validator = DataValidator()
    results = validator.validate_directory(data_dir)
    
    # Log results
    valid_count = sum(1 for result in results.values() if result.is_valid)
    total_count = len(results)
    
    logger.info(f"Validation complete: {valid_count}/{total_count} files valid")
    
    for filename, result in results.items():
        if result.is_valid:
            logger.info(f"✓ {filename}: Valid ({result.row_count} rows)")
        else:
            logger.warning(f"✗ {filename}: {len(result.errors)} errors")
    
    return results


if __name__ == "__main__":
    # Run the main pipeline
    result = data_ingestion_pipeline()
    print(f"Pipeline completed: {result}")