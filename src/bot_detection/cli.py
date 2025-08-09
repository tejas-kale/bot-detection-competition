"""Command-line interface for the data ingestion pipeline."""

import argparse
import logging
import sys
from pathlib import Path

from .config import get_settings, setup_gcp_credentials, setup_kaggle_credentials
from .flows import data_ingestion_pipeline, validate_existing_data_flow


def setup_logging(level: str = "INFO") -> None:
    """Set up logging configuration."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ]
    )


def run_pipeline(environment: str) -> None:
    """Run the complete data ingestion pipeline."""
    print(f"🚀 Starting data ingestion pipeline for environment: {environment}")
    
    try:
        result = data_ingestion_pipeline(environment)
        
        print("\n✅ Pipeline completed successfully!")
        print(f"📁 Unified dataset: {result['unified_dataset_path']}")
        print(f"☁️  GCS URL: {result['gcs_url']}")
        print(f"📋 Metadata: {result['metadata_path']}")
        
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        sys.exit(1)


def validate_data(data_directory: str = None) -> None:
    """Validate existing data files."""
    print("🔍 Validating existing data files...")
    
    try:
        results = validate_existing_data_flow(data_directory)
        
        valid_count = sum(1 for result in results.values() if result.is_valid)
        total_count = len(results)
        
        print(f"\n📊 Validation Results: {valid_count}/{total_count} files valid")
        
        for filename, result in results.items():
            status = "✅" if result.is_valid else "❌"
            print(f"{status} {filename}: {result.row_count} rows, {result.column_count} columns")
            
            if not result.is_valid:
                for error in result.errors[:3]:  # Show first 3 errors
                    print(f"   - {error}")
                if len(result.errors) > 3:
                    print(f"   - ... and {len(result.errors) - 3} more errors")
        
    except Exception as e:
        print(f"\n❌ Validation failed: {e}")
        sys.exit(1)


def check_credentials(environment: str) -> None:
    """Check that all required credentials are properly configured."""
    print(f"🔐 Checking credentials for environment: {environment}")
    
    try:
        settings = get_settings(environment)
        
        # Check GCP credentials
        try:
            setup_gcp_credentials(settings)
            print("✅ GCP credentials configured")
        except Exception as e:
            print(f"❌ GCP credentials issue: {e}")
        
        # Check Kaggle credentials
        try:
            setup_kaggle_credentials(settings)
            print("✅ Kaggle credentials configured")
        except Exception as e:
            print(f"❌ Kaggle credentials issue: {e}")
        
        # Check bucket access
        from .gcs_storage import GCSStorageManager
        try:
            storage_manager = GCSStorageManager(settings)
            print(f"✅ GCS bucket accessible: {settings.gcp_bucket_name}")
        except Exception as e:
            print(f"❌ GCS bucket issue: {e}")
        
        print(f"\n📋 Configuration summary:")
        print(f"   Environment: {settings.environment}")
        print(f"   GCP Project: {settings.gcp_project_id}")
        print(f"   GCS Bucket: {settings.gcp_bucket_name}")
        print(f"   Log Level: {settings.log_level}")
        
    except Exception as e:
        print(f"\n❌ Credentials check failed: {e}")
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Bot Detection Data Ingestion Pipeline")
    parser.add_argument(
        "--environment", "-e", 
        choices=["dev", "prod"], 
        default="dev",
        help="Environment to use (dev/prod)"
    )
    parser.add_argument(
        "--log-level", "-l",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Pipeline command
    pipeline_parser = subparsers.add_parser("run", help="Run the complete data ingestion pipeline")
    
    # Validation command
    validate_parser = subparsers.add_parser("validate", help="Validate existing data files")
    validate_parser.add_argument(
        "--directory", "-d",
        help="Directory to validate (defaults to data/raw)"
    )
    
    # Credentials check command
    creds_parser = subparsers.add_parser("check-creds", help="Check credentials configuration")
    
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(args.log_level)
    
    # Execute command
    if args.command == "run":
        run_pipeline(args.environment)
    elif args.command == "validate":
        validate_data(args.directory)
    elif args.command == "check-creds":
        check_credentials(args.environment)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()