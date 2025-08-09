output "storage_bucket_name" {
  description = "Name of the created storage bucket"
  value       = google_storage_bucket.data_storage.name
}

output "storage_bucket_url" {
  description = "URL of the created storage bucket"
  value       = google_storage_bucket.data_storage.url
}

output "service_account_email" {
  description = "Email of the service account"
  value       = google_service_account.data_pipeline.email
}

output "project_id" {
  description = "The project ID"
  value       = data.google_project.current.project_id
}