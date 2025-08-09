"""Data ingestion module for downloading and processing competition datasets."""

import logging
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import kaggle
import pandas as pd
from google.cloud import storage
from pydantic import BaseModel, Field

from .config import Settings, setup_kaggle_credentials

logger = logging.getLogger(__name__)


class DatasetInfo(BaseModel):
    """Information about a dataset to be downloaded."""
    
    competition: Optional[str] = None
    dataset: Optional[str] = None
    name: str = Field(..., description="Human-readable name for the dataset")
    files: List[str] = Field(default_factory=list, description="Specific files to download")


class DataIngestionPipeline:
    """Pipeline for downloading and processing datasets."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.project_root = Path(__file__).parent.parent.parent
        self.data_dir = self.project_root / "data"
        
        # Set up directory structure
        self.raw_dir = self.data_dir / "raw"
        self.interim_dir = self.data_dir / "interim"
        self.processed_dir = self.data_dir / "processed"
        self.external_dir = self.data_dir / "external"
        
        # Create directories
        for dir_path in [self.raw_dir, self.interim_dir, self.processed_dir, self.external_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Set up Kaggle credentials
        setup_kaggle_credentials(settings)
        
        # Set up GCP client
        if settings.google_application_credentials:
            self.storage_client = storage.Client(project=settings.gcp_project_id)
            self.bucket = self.storage_client.bucket(settings.gcp_bucket_name)
        else:
            self.storage_client = None
            self.bucket = None
    
    def download_competition_data(self, competition: str, download_path: Path) -> List[Path]:
        """Download data from a Kaggle competition."""
        logger.info(f"Downloading competition data: {competition}")
        
        try:
            # Create temporary download directory
            temp_dir = download_path / "temp"
            temp_dir.mkdir(exist_ok=True)
            
            # Download competition files
            kaggle.api.competition_download_files(
                competition, 
                path=str(temp_dir), 
                quiet=False
            )
            
            # Extract zip files
            downloaded_files = []
            for zip_file in temp_dir.glob("*.zip"):
                logger.info(f"Extracting {zip_file.name}")
                with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                    zip_ref.extractall(download_path)
                
                # List extracted files
                with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                    extracted = [download_path / name for name in zip_ref.namelist()]
                    downloaded_files.extend(extracted)
            
            # Clean up temp directory
            shutil.rmtree(temp_dir)
            
            logger.info(f"Downloaded {len(downloaded_files)} files from competition {competition}")
            return downloaded_files
            
        except Exception as e:
            logger.error(f"Error downloading competition {competition}: {e}")
            raise
    
    def download_dataset(self, dataset: str, download_path: Path) -> List[Path]:
        """Download data from a Kaggle dataset."""
        logger.info(f"Downloading dataset: {dataset}")
        
        try:
            # Create temporary download directory
            temp_dir = download_path / "temp"
            temp_dir.mkdir(exist_ok=True)
            
            # Download dataset files
            kaggle.api.dataset_download_files(
                dataset, 
                path=str(temp_dir), 
                quiet=False
            )
            
            # Extract zip files
            downloaded_files = []
            for zip_file in temp_dir.glob("*.zip"):
                logger.info(f"Extracting {zip_file.name}")
                with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                    zip_ref.extractall(download_path)
                
                # List extracted files
                with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                    extracted = [download_path / name for name in zip_ref.namelist()]
                    downloaded_files.extend(extracted)
            
            # Clean up temp directory
            shutil.rmtree(temp_dir)
            
            logger.info(f"Downloaded {len(downloaded_files)} files from dataset {dataset}")
            return downloaded_files
            
        except Exception as e:
            logger.error(f"Error downloading dataset {dataset}: {e}")
            raise
    
    def download_datasets(self, datasets: List[DatasetInfo]) -> Dict[str, List[Path]]:
        """Download multiple datasets."""
        logger.info(f"Starting download of {len(datasets)} datasets")
        
        downloaded_data = {}
        
        for dataset_info in datasets:
            dataset_dir = self.raw_dir / dataset_info.name.replace(" ", "_").lower()
            dataset_dir.mkdir(exist_ok=True)
            
            try:
                if dataset_info.competition:
                    files = self.download_competition_data(dataset_info.competition, dataset_dir)
                elif dataset_info.dataset:
                    files = self.download_dataset(dataset_info.dataset, dataset_dir)
                else:
                    raise ValueError(f"Dataset {dataset_info.name} must specify either competition or dataset")
                
                downloaded_data[dataset_info.name] = files
                logger.info(f"Successfully downloaded {dataset_info.name}")
                
            except Exception as e:
                logger.error(f"Failed to download {dataset_info.name}: {e}")
                downloaded_data[dataset_info.name] = []
        
        return downloaded_data
    
    def upload_to_gcs(self, local_path: Path, gcs_path: str) -> str:
        """Upload a file to Google Cloud Storage."""
        if not self.bucket:
            raise ValueError("GCS bucket not configured")
        
        logger.info(f"Uploading {local_path} to gs://{self.settings.gcp_bucket_name}/{gcs_path}")
        
        blob = self.bucket.blob(gcs_path)
        blob.upload_from_filename(str(local_path))
        
        return f"gs://{self.settings.gcp_bucket_name}/{gcs_path}"
    
    def create_data_version(self) -> str:
        """Create a version string for the current data ingestion run."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{self.settings.data_version_prefix}{timestamp}"
    
    def get_competition_datasets(self) -> List[DatasetInfo]:
        """Get the list of datasets to download for the competition."""
        return [
            DatasetInfo(
                competition="llm-detect-ai-generated-text",
                name="primary_competition_data"
            ),
            DatasetInfo(
                dataset="thedrcat/daigt-v2-train-dataset",
                name="daigt_v2_additional_data"
            )
        ]