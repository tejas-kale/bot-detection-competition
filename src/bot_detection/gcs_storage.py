"""Google Cloud Storage integration for data pipeline."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from google.cloud import storage
from google.cloud.exceptions import NotFound
from pydantic import BaseModel

from .config import Settings

logger = logging.getLogger(__name__)


class GCSFileInfo(BaseModel):
    """Information about a file in Google Cloud Storage."""
    
    name: str
    size: int
    created: datetime
    updated: datetime
    generation: int
    metageneration: int
    content_type: str


class GCSStorageManager:
    """Manager for Google Cloud Storage operations."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = storage.Client(project=settings.gcp_project_id)
        self.bucket = self.client.bucket(settings.gcp_bucket_name)
        
        # Verify bucket exists
        self._verify_bucket()
    
    def _verify_bucket(self) -> None:
        """Verify that the GCS bucket exists and is accessible."""
        try:
            self.bucket.reload()
            logger.info(f"Connected to GCS bucket: {self.settings.gcp_bucket_name}")
        except NotFound:
            raise ValueError(f"GCS bucket not found: {self.settings.gcp_bucket_name}")
        except Exception as e:
            raise ValueError(f"Cannot access GCS bucket {self.settings.gcp_bucket_name}: {e}")
    
    def upload_file(self, local_path: Path, gcs_path: str, metadata: Optional[Dict[str, str]] = None) -> str:
        """Upload a file to Google Cloud Storage."""
        if not local_path.exists():
            raise FileNotFoundError(f"Local file not found: {local_path}")
        
        logger.info(f"Uploading {local_path} to gs://{self.settings.gcp_bucket_name}/{gcs_path}")
        
        blob = self.bucket.blob(gcs_path)
        
        # Set metadata if provided
        if metadata:
            blob.metadata = metadata
        
        # Set content type based on file extension
        content_type = self._get_content_type(local_path.suffix)
        blob.content_type = content_type
        
        # Upload the file
        blob.upload_from_filename(str(local_path))
        
        gcs_url = f"gs://{self.settings.gcp_bucket_name}/{gcs_path}"
        logger.info(f"Successfully uploaded to: {gcs_url}")
        
        return gcs_url
    
    def download_file(self, gcs_path: str, local_path: Path) -> Path:
        """Download a file from Google Cloud Storage."""
        logger.info(f"Downloading gs://{self.settings.gcp_bucket_name}/{gcs_path} to {local_path}")
        
        blob = self.bucket.blob(gcs_path)
        
        if not blob.exists():
            raise NotFound(f"File not found in GCS: {gcs_path}")
        
        # Create local directory if it doesn't exist
        local_path.parent.mkdir(parents=True, exist_ok=True)
        
        blob.download_to_filename(str(local_path))
        
        logger.info(f"Successfully downloaded to: {local_path}")
        return local_path
    
    def list_files(self, prefix: str = "", delimiter: str = None) -> List[GCSFileInfo]:
        """List files in the GCS bucket."""
        logger.info(f"Listing files with prefix: {prefix}")
        
        blobs = self.client.list_blobs(
            self.bucket.name, 
            prefix=prefix, 
            delimiter=delimiter
        )
        
        file_infos = []
        for blob in blobs:
            file_info = GCSFileInfo(
                name=blob.name,
                size=blob.size,
                created=blob.time_created,
                updated=blob.updated,
                generation=blob.generation,
                metageneration=blob.metageneration,
                content_type=blob.content_type or "application/octet-stream"
            )
            file_infos.append(file_info)
        
        logger.info(f"Found {len(file_infos)} files")
        return file_infos
    
    def delete_file(self, gcs_path: str) -> bool:
        """Delete a file from Google Cloud Storage."""
        logger.info(f"Deleting gs://{self.settings.gcp_bucket_name}/{gcs_path}")
        
        blob = self.bucket.blob(gcs_path)
        
        if not blob.exists():
            logger.warning(f"File not found, cannot delete: {gcs_path}")
            return False
        
        blob.delete()
        logger.info(f"Successfully deleted: {gcs_path}")
        return True
    
    def copy_file(self, source_gcs_path: str, dest_gcs_path: str) -> str:
        """Copy a file within Google Cloud Storage."""
        logger.info(f"Copying {source_gcs_path} to {dest_gcs_path}")
        
        source_blob = self.bucket.blob(source_gcs_path)
        
        if not source_blob.exists():
            raise NotFound(f"Source file not found: {source_gcs_path}")
        
        dest_blob = self.bucket.copy_blob(source_blob, self.bucket, dest_gcs_path)
        
        gcs_url = f"gs://{self.settings.gcp_bucket_name}/{dest_gcs_path}"
        logger.info(f"Successfully copied to: {gcs_url}")
        
        return gcs_url
    
    def get_file_info(self, gcs_path: str) -> Optional[GCSFileInfo]:
        """Get information about a file in Google Cloud Storage."""
        blob = self.bucket.blob(gcs_path)
        
        if not blob.exists():
            return None
        
        blob.reload()  # Fetch metadata
        
        return GCSFileInfo(
            name=blob.name,
            size=blob.size,
            created=blob.time_created,
            updated=blob.updated,
            generation=blob.generation,
            metageneration=blob.metageneration,
            content_type=blob.content_type or "application/octet-stream"
        )
    
    def create_signed_url(self, gcs_path: str, expiration_minutes: int = 60) -> str:
        """Create a signed URL for temporary access to a file."""
        from datetime import timedelta
        
        blob = self.bucket.blob(gcs_path)
        
        if not blob.exists():
            raise NotFound(f"File not found: {gcs_path}")
        
        expiration = datetime.utcnow() + timedelta(minutes=expiration_minutes)
        
        url = blob.generate_signed_url(
            expiration=expiration,
            method='GET'
        )
        
        logger.info(f"Generated signed URL for {gcs_path}, expires in {expiration_minutes} minutes")
        return url
    
    def upload_dataset_with_versioning(self, local_path: Path, dataset_name: str, 
                                     version: str, metadata: Optional[Dict[str, str]] = None) -> str:
        """Upload a dataset with proper versioning structure."""
        # Create versioned path structure
        gcs_path = f"datasets/{dataset_name}/{version}/{local_path.name}"
        
        # Add version metadata
        upload_metadata = {
            "dataset_name": dataset_name,
            "version": version,
            "upload_timestamp": datetime.now().isoformat(),
            "environment": self.settings.environment
        }
        
        if metadata:
            upload_metadata.update(metadata)
        
        return self.upload_file(local_path, gcs_path, upload_metadata)
    
    def list_dataset_versions(self, dataset_name: str) -> List[str]:
        """List all versions of a dataset."""
        prefix = f"datasets/{dataset_name}/"
        
        blobs = self.client.list_blobs(self.bucket.name, prefix=prefix, delimiter="/")
        
        # Extract version directories
        versions = []
        for prefix_obj in blobs.prefixes:
            # Extract version from path like "datasets/dataset_name/v20231201_123456/"
            version = prefix_obj.rstrip("/").split("/")[-1]
            versions.append(version)
        
        # Sort versions (assuming they follow a sortable format)
        versions.sort(reverse=True)  # Latest first
        
        logger.info(f"Found {len(versions)} versions for dataset {dataset_name}")
        return versions
    
    def get_latest_dataset_version(self, dataset_name: str) -> Optional[str]:
        """Get the latest version of a dataset."""
        versions = self.list_dataset_versions(dataset_name)
        return versions[0] if versions else None
    
    def _get_content_type(self, file_extension: str) -> str:
        """Get content type based on file extension."""
        content_types = {
            '.csv': 'text/csv',
            '.parquet': 'application/octet-stream',
            '.json': 'application/json',
            '.txt': 'text/plain',
            '.md': 'text/markdown'
        }
        
        return content_types.get(file_extension.lower(), 'application/octet-stream')