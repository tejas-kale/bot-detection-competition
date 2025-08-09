"""Bot Detection Competition Package"""

__version__ = "0.1.0"

from .config import Settings, get_settings
from .data_ingestion import DataIngestionPipeline, DatasetInfo
from .data_unification import DataUnifier
from .data_validation import DataValidator, ValidationResult
from .flows import data_ingestion_pipeline, validate_existing_data_flow
from .gcs_storage import GCSStorageManager

__all__ = [
    "Settings",
    "get_settings", 
    "DataIngestionPipeline",
    "DatasetInfo",
    "DataUnifier", 
    "DataValidator",
    "ValidationResult",
    "data_ingestion_pipeline",
    "validate_existing_data_flow",
    "GCSStorageManager",
]