# Production Transition Notes

This file documents items that need modification for production readiness.

## Infrastructure

### Terraform Configuration
- [ ] Update `terraform/terraform.tfvars` with production project ID and region
- [ ] Review bucket lifecycle policies for production data retention requirements
- [ ] Configure production service account with minimal required permissions
- [ ] Set `force_destroy = false` for production GCS bucket to prevent accidental deletion
- [ ] Enable audit logging for production GCS bucket access

### Environment Configuration  
- [ ] Create production `.env.prod` file with production GCS bucket names
- [ ] Configure production Prefect server URL (replace local development server)
- [ ] Set production log level to WARNING to reduce log volume
- [ ] Update data version prefix strategy for production releases

## Security
- [ ] Remove development service account key generation in production Terraform
- [ ] Use workload identity or IAM service account impersonation instead of key files
- [ ] Review and restrict GCS bucket IAM permissions to minimum required access
- [ ] Enable GCS uniform bucket-level access enforcement

## Data Pipeline
- [ ] Configure production data retention and archival policies
- [ ] Set up monitoring and alerting for pipeline failures in production
- [ ] Review dataset download quotas and rate limiting for Kaggle API
- [ ] Implement production data backup and disaster recovery procedures

## Monitoring
- [ ] Configure production Prefect Cloud deployment with proper authentication
- [ ] Set up structured logging with appropriate log aggregation service
- [ ] Configure production alerting for data validation failures
- [ ] Implement data quality monitoring dashboards