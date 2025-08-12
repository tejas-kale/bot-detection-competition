# MLOps Project Configuration

## Project Overview
This is an MLOps competition project focused on building a comprehensive machine learning pipeline with proper orchestration, reproducibility, and best practices.

## Technical Stack & Preferences

### Infrastructure Management
- **Infrastructure as Code**: All cloud resources must be managed using Terraform
- **Cloud Provider**: Google Cloud Platform (GCP)
- **Authentication**: Use `gcloud auth login` and `gcloud auth application-default login` for local development
- **Project**: Work with the default GCP project configured in gcloud CLI
- **Best Practices**: Apply your knowledge of GCP and Terraform best practices for resource naming, organization, and security

### Orchestration & Workflow Management
- **Primary Orchestration Tool**: Prefect for all pipeline workflows
- **Execution Environment**: Run Prefect locally for development
- **Scheduling**: Support both manual triggers and scheduled execution capability

### Data Management
- **Storage Format**: Prefer Parquet for structured data storage
- **Cloud Storage**: GCP Cloud Storage with versioning enabled
- **Data Versioning**: Implement systematic dataset versioning strategy
- **Validation**: Comprehensive data quality and schema validation

### Development Practices
- **Code Organisation**: Modular, reusable components following software engineering best practices
- **Package Management**: Use `uv` package manager with dependencies specified in `pyproject.toml`
- **Code Formatting**: All Python files must be formatted with `black` before committing
- **Code Linting**: All Python files must be checked with `flake8` and linting errors fixed before committing
- **Configuration Management**: Support two environments - `dev` and `prod`
- **Environment Variables**: Use `.env` template files for managing environment-specific configurations
- **Current Environment**: All development work should target `dev` environment
- **Production Planning**: When encountering code or configurations that need modification for production readiness, document these items in `.github/prod-transition-notes.md` as a simple checklist with one-sentence explanations if needed
- **Error Handling**: Prioritise failing fast with clear error messages during project setup phase
- **Logging**: Set up structured logging from the start with consistent log levels and formats across all components

### Security & Compliance
- **Secrets Management**: Secure handling of API keys, credentials, and sensitive data
- **Access Control**: Apply principle of least privilege using GCP IAM best practices

## Project Structure Preferences
Use your best judgment to organise code in a logical, maintainable structure with clear separation of concerns.

### Standardised Data Directory Structure
Create and maintain the following directory structure for data management:
```
data/
├── raw/           # Original, immutable data
├── interim/       # Intermediate data that has been transformed
├── processed/     # Final, analysis-ready datasets
└── external/      # Data from third-party sources
```

## Quality Standards
- All code must be properly documented with both inline docstrings and separate documentation files
- Use British English throughout the project (code comments, documentation, variable names, etc.)
- Infrastructure changes must be reproducible and version-controlled
- Data pipelines must be deterministic and auditable
- Error handling and recovery mechanisms are essential
- Follow established software engineering principles

## Autonomous Operations

### Operations That Can Be Performed Automatically
Claude Code can execute the following operations without requesting permission:

- **Git Operations**: Creating feature branches, making commits, merging, rebasing, pushing feature branches to GitHub
- **Branch Management**: Creating new feature branches for each user story (never work on main directly)
- **File Operations**: Creating, modifying, deleting files and directories
- **Package Management**: Installing, updating, removing Python packages using `uv`
- **Code Quality**: Running `black` to format Python files and `flake8` to check for linting errors
- **Script Execution**: Running Python scripts that Claude Code writes
- **Infrastructure Planning**: Running `terraform plan` and `terraform validate`
- **Documentation Generation**: Creating and updating documentation files
- **Pull Request Creation**: Creating PRs from feature branches to main branch

### Operations Requiring Confirmation
- **Infrastructure Changes**: `terraform apply` or `terraform destroy` operations
- **External API Calls**: Operations that consume external services or credits
- **System-Level Changes**: Modifications to system-wide configurations

### Git Workflow
- **Branch Creation**: Always create a new feature branch before starting work on any user story (naming: `feature/user-story-[number]-[short-description]`)
- **Never work directly on main branch** - all development must happen on feature branches
- Make frequent commits during development for easy reverting
- **Pre-commit Quality Checks**: Before each commit, ensure all Python files are formatted with `black` and pass `flake8` linting checks
- After completing user story implementation:
  1. Run final code quality checks (`black` formatting and `flake8` linting)
  2. Squash all commits into a single, well-described commit on the feature branch
  3. Push the feature branch to GitHub
  4. **Always create a Pull Request** from the feature branch to main with comprehensive description of changes
  5. Do not merge the PR automatically - leave it open for review

## Documentation Requirements
After completing each user story, create a tutorial document explaining the implementation:

- **Format**: Markdown file in `tutorials/` directory
- **Naming**: Check existing tutorial files and increment number by 1 (e.g., if `00-setup.md` exists, create `01-data-ingestion.md`)
- **Audience**: First-year Computer Science undergraduates
- **Style**: Extremely concise, no fluff, focus on concrete steps and technical concepts
- **Content**: Step-by-step explanation of what was implemented and why, reading as an independent blog post
- **Technical Depth**: Explain key concepts but assume basic programming knowledge
- **Language**: Use British English throughout

## Current User Story Context
[User story details will be provided in the prompt to give specific implementation context]