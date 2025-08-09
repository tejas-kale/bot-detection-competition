terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

# Configure the Google Cloud Provider
provider "google" {
  project = var.project_id
  region  = var.region
}

# Data source to get current project information
data "google_project" "current" {}

# Cloud Storage bucket for data storage
resource "google_storage_bucket" "data_storage" {
  name                        = "${var.project_id}-bot-detection-data-${var.environment}"
  location                    = var.region
  force_destroy              = var.environment == "dev" ? true : false
  uniform_bucket_level_access = true
  
  # Enable versioning for data lineage
  versioning {
    enabled = true
  }
  
  # Lifecycle management
  lifecycle_rule {
    condition {
      age = var.environment == "dev" ? 30 : 90
    }
    action {
      type = "Delete"
    }
  }
  
  # Public access prevention
  public_access_prevention = "enforced"
  
  labels = {
    environment = var.environment
    project     = "bot-detection-competition"
    managed_by  = "terraform"
  }
}

# Service account for data pipeline operations
resource "google_service_account" "data_pipeline" {
  account_id   = "bot-detection-pipeline-${var.environment}"
  display_name = "Bot Detection Data Pipeline Service Account (${var.environment})"
  description  = "Service account for bot detection data pipeline operations"
}

# Grant necessary permissions to the service account
resource "google_storage_bucket_iam_member" "data_pipeline_storage_admin" {
  bucket = google_storage_bucket.data_storage.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.data_pipeline.email}"
}

# Create a service account key for local development (dev environment only)
resource "google_service_account_key" "data_pipeline_key" {
  count              = var.environment == "dev" ? 1 : 0
  service_account_id = google_service_account.data_pipeline.name
  public_key_type    = "TYPE_X509_PEM_FILE"
}

# Store the service account key as a local file (dev environment only)
resource "local_file" "service_account_key" {
  count           = var.environment == "dev" ? 1 : 0
  content         = base64decode(google_service_account_key.data_pipeline_key[0].private_key)
  filename        = "${path.root}/../config/gcp-service-account-${var.environment}.json"
  file_permission = "0600"
}