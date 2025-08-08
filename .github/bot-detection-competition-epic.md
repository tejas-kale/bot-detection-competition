# **Epic: AI-Generated Text Detection System**

**Goal:** To design, build, deploy, and monitor a highly accurate machine learning system capable of distinguishing between human-written and AI-generated text. This system will be developed as a **high-quality portfolio project by a solo senior developer** for the MLOps Zoomcamp competition, with an initial goal of achieving a top-50 rank on the associated Kaggle leaderboard.  

**Scope:** The project covers the full MLOps lifecycle, from data ingestion to a fully monitored production system. The primary focus is on delivering a **robust, backend-only REST API**. There are no plans for a user-facing web application. Development will prioritise **cost-effective GCP services** (e.g., Cloud Run, Cloud Storage) to minimise expenses. The system will leverage existing external datasets for training and evaluation, and model explainability will be addressed using post-hoc methods. The primary cloud platform will be Google Cloud Platform (GCP), and workflow orchestration will be managed by Prefect.

## **1. User Story: Project Scaffolding & Initial Exploratory Data Analysis (EDA)**

**Objective:** To establish the foundational project structure and conduct an initial EDA to understand the data's characteristics, distributions, and potential challenges.  

**Context:** Before any development begins, we need a clean, reproducible project structure. This includes setting up version control, defining the environment, and performing a first-pass analysis of the primary Kaggle dataset to form initial hypotheses about feature engineering and model selection.  

**Acceptance Criteria:**
* A Git repository is initialised with a standard project structure (src, notebooks, tests, data).  
* A pyproject.toml file is created to manage dependencies.  
* An EDA notebook is created that analyses the primary training data.  
* The notebook contains visualisations and summaries of text length, word counts, punctuation usage, and class balance (human vs. AI).  
* Key findings and initial hypotheses are documented in a summary markdown file.

**MLOps Competition Criteria Fulfilled:**
* **Problem Framing & EDA:** Directly addresses the need for thorough data exploration.  
* **Reproducibility:** Establishes a consistent environment.  
* **Best Practices:** Implements standard project structure and version control.

## **2. User Story: Automated Data Ingestion & Unification Pipeline**

**Objective:** To create a reliable, automated pipeline that fetches, validates, and unifies all required datasets into a single, analysis-ready format.  

**Context:** High-performing models require diverse data. We need to combine the original Kaggle training set with the additional provided datasets. This process must be automated to ensure consistency and to easily incorporate new data sources in the future.  

**Acceptance Criteria:**
* A script is developed to download the primary Kaggle dataset and the additional daigt-v2-train-dataset.  
* The script validates the downloaded data against expected schemas (e.g., column names, data types).  
* The script unifies all datasets into a single Parquet or CSV file, handling any differences in column names or formats.  
* The unified dataset is stored in a versioned GCP Cloud Storage bucket.  
* The entire process is encapsulated in a function that can be triggered manually.

**MLOps Competition Criteria Fulfilled:**
* **Workflow Orchestration:** Lays the groundwork for an automated data pipeline.  
* **Reproducibility:** Ensures the data preparation process is script-based and repeatable.  
* **Best Practices:** Modular code for data ingestion.

## **3. User Story: Feature Engineering & Preprocessing Flow**

**Objective:** To develop a preprocessing and feature engineering pipeline that transforms raw text into meaningful numerical features for the model.  

**Context:** The raw text is not directly usable by most ML models. We need to create features that capture the stylistic and structural differences between human and AI writing. This flow should be designed as a reusable component of the overall training pipeline.  

**Acceptance Criteria:**
* A preprocessing module is created that cleans text (e.g., lowercasing, removing special characters).  
* Feature engineering functions are implemented to extract features like:  
  * **Lexical Features:** TF-IDF vectors, n-gram frequencies.  
  * **Syntactic Features:** Punctuation counts, sentence length statistics, part-of-speech tag frequencies.  
  * **Readability Scores:** Flesch-Kincaid, Gunning-Fog index.  
* The entire feature extraction process is saved as a scikit-learn pipeline or equivalent object.  
* The feature pipeline object is versioned and stored in the GCP Cloud Storage bucket alongside the data.

**MLOps Competition Criteria Fulfilled:**

* **Model Development:** Core part of preparing data for modelling.  
* **Reproducibility:** The saved pipeline ensures identical feature transformations during training and inference.

## **4. User Story: Baseline Model Training & Evaluation**

**Objective:** To train and evaluate a simple, interpretable baseline model to establish a minimum performance benchmark.  

**Context:** We must first establish a performance baseline. A simple model like Logistic Regression or a LightGBM classifier serves as a sanity check and provides a benchmark against which more complex models can be compared.  

**Acceptance Criteria:**
* A training script is created that loads the preprocessed data and features.  
* The script trains a Logistic Regression or LightGBM model.  
* The model is evaluated using cross-validation on the training set.  
* Performance metrics (AUC, F1-score, Accuracy, Precision, Recall) are calculated and logged to the console or a local file.  
* The trained model object and its performance metrics are saved to a local directory.

**MLOps Competition Criteria Fulfilled:**
* **Model Development:** The first iteration of the modelling cycle.  
* **Evaluation:** Establishes a clear, metric-driven evaluation process.

## **5. User Story: Experiment Tracking with MLflow**

**Objective:** To integrate MLflow for logging and comparing all model training experiments systematically.  

**Context:** As we experiment with different features, models, and hyperparameters, we need a robust system to track what we've done. MLflow will allow us to log parameters, metrics, and model artifacts, making our experiments organised and reproducible.  

**Acceptance Criteria:**
* MLflow is added as a project dependency.  
* The training script from the previous story is modified to use MLflow.  
* Each run logs:  
  * Parameters (e.g., model type, feature set version).  
  * Metrics (AUC, F1-score, etc.).  
  * Artifacts (trained model object, feature pipeline, confusion matrix plot).  
* A local MLflow tracking server can be launched to view and compare experiment results.

**MLOps Competition Criteria Fulfilled:**
* **Experiment Tracking:** This is the core implementation of experiment tracking.  
* **Reproducibility:** MLflow helps trace any model back to the code and data that produced it.

## **6. User Story: Advanced Model Development & Hyperparameter Tuning**

**Objective:** To develop a more sophisticated model and use automated hyperparameter tuning to maximise its predictive performance.  

**Context:** To be competitive, we need to move beyond the baseline. This involves using more powerful algorithms (e.g., ensemble models, transformers) and systematically searching for the best hyperparameter configuration.  

**Acceptance Criteria:**
* An advanced model (e.g., an ensemble of LightGBM and a simple transformer-based classifier like DeBERTa) is implemented.  
* A hyperparameter tuning script is created using a library like Hyperopt or Optuna.  
* The tuning process is integrated with MLflow to track each trial as a nested run.  
* The best model from the tuning process is identified and registered in the MLflow Model Registry.  
* The final model's performance on a hold-out test set exceeds the baseline model's performance by a significant margin (e.g., \>5% improvement in AUC).

**MLOps Competition Criteria Fulfilled:**
* **Model Development:** Focuses on creating a state-of-the-art model.  
* **Experiment Tracking:** Leverages MLflow for advanced use cases like HPO and model registration.

## **7. User Story: Batch Prediction & Kaggle Submission Pipeline**

**Objective:** To create an automated pipeline that generates predictions on the Kaggle test set and formats them for submission.  

**Context:** To participate in the competition, we need a repeatable process for generating predictions on the official test data using our best-registered model.  

**Acceptance Criteria:**
* A script is created that loads a registered model from the MLflow Model Registry.  
* The script downloads the Kaggle test set, applies the corresponding feature engineering pipeline, and generates predictions.  
* The predictions are formatted into a submission.csv file with the required columns (id, generated).  
* The entire process can be run from a single command.

**MLOps Competition Criteria Fulfilled:**

* **Workflow Orchestration:** A key automated workflow for the competition.  
* **Reproducibility:** Ensures submissions can be recreated perfectly.

## **8. User Story: Model Deployment as a REST API on GCP Cloud Run**

**Objective:** To deploy the best-performing model as a scalable, serverless REST API for real-time predictions.  

**Context:** A key MLOps goal is to make the model accessible. Deploying it as a web service allows other applications to get predictions via a simple API call. GCP Cloud Run is a cost-effective, scalable choice for this.  

**Acceptance Criteria:**
* A web service is created using FastAPI or Flask.  
* The service has a /predict endpoint that accepts a block of text.  
* The endpoint loads the registered model from MLflow and returns a JSON response with the prediction (e.g., {"is\_ai\_generated": 1, "confidence\_score": 0.92}).  
* A Dockerfile is created to containerise the service.  
* The container is successfully deployed to GCP Cloud Run.

**MLOps Competition Criteria Fulfilled:**
* **Model Deployment:** The core task of making the model available as a service.  
* **Best Practices:** Uses containerisation for portable deployments.

## **9. User Story: Input/Output Guardrails for the Prediction Service**

**Objective:** To implement safety checks within the API to handle invalid inputs and ensure reliable outputs.  

**Context:** A production service must be robust against unexpected inputs. We need to add guardrails to validate incoming data and format the output consistently, preventing errors and ensuring the service is reliable.  

**Acceptance Criteria:**
* **Input Guardrail:** The /predict endpoint validates the input payload. It rejects requests that do not contain text or where the text is too short/long, returning a clear 4xx error code.  
* **Output Guardrail:** The prediction logic is wrapped in a try...except block. If the model fails to produce a prediction, the API returns a consistent 5xx error message instead of crashing.  
* The API's data validation logic is handled using Pydantic models.

**MLOps Competition Criteria Fulfilled:**
* **Safety:** Directly implements input and output guardrails.  
* **Best Practices:** Enhances the robustness of the production service.

## **10. User Story: Orchestrate the Full Training Pipeline with Prefect**

**Objective:** To convert the entire model training workflow—from data ingestion to model registration—into a Prefect flow.  

**Context:** Manually running scripts is error-prone. We will use Prefect to define our training pipeline as a Directed Acyclic Graph (DAG) of tasks. This makes the workflow observable, repeatable, and easier to schedule.  

**Acceptance Criteria:**
* The data ingestion, feature engineering, training, and model registration scripts are refactored into Prefect tasks.  
* A main Prefect flow (@flow) is created that defines the dependencies between these tasks.  
* The flow can be executed locally using prefect run.  
* The flow successfully runs from end-to-end, resulting in a new model being registered in MLflow.  
* The Prefect flow is configured to use GCP Cloud Storage for storing intermediate artifacts.

**MLOps Competition Criteria Fulfilled:**
* **Workflow Orchestration:** The primary implementation of a workflow orchestrator.  
* **Reproducibility:** The entire training process is now codified and automated.

## **11. User Story: CI/CD Pipeline for Automated Testing & Deployment**

**Objective:** To set up a CI/CD pipeline that automatically tests and deploys changes to the prediction service.  

**Context:** To maintain quality and velocity, we need to automate our testing and deployment processes. Every change pushed to the main branch should be tested, and if successful, the API on Cloud Run should be updated automatically.  

**Acceptance Criteria:**
* Unit tests are written for the feature engineering logic and the API endpoints.  
* A GitHub Actions (or GCP Cloud Build) workflow is configured.  
* The workflow is triggered on every push to the main branch.  
* The CI pipeline runs all unit tests.  
* If tests pass, the CD pipeline builds a new Docker image and deploys it to GCP Cloud Run.

**MLOps Competition Criteria Fulfilled:**

* **CI/CD:** A complete implementation of CI/CD for an ML service.  
* **Best Practices:** Enforces a culture of automated testing and deployment.

## **12. User Story: Model & Data Drift Monitoring Dashboard**

**Objective:** To create a dashboard for monitoring the deployed model's performance and detecting data drift.  

**Context:** A model's performance can degrade over time as the input data changes. We need to monitor the predictions made by our API and compare their statistical properties to the training data to detect drift.  

**Acceptance Criteria:**
* The prediction service logs every incoming request (the features) and the model's prediction to a GCP BigQuery table.  
* A scheduled job (e.g., a Prefect flow or Cloud Function) runs daily to analyse the production data.  
* The job calculates metrics on the production data (e.g., distribution of text lengths, punctuation frequency) and compares them to the training data's statistics.  
* A data drift report is generated using a library like Evidently AI or scipy.stats.ks\_2samp.  
* The results are visualised in a GCP Looker Studio (or Grafana) dashboard.  
* An alert is configured to trigger if the drift score exceeds a predefined threshold.

**MLOps Competition Criteria Fulfilled:**
* **Monitoring:** Implements both data and model performance monitoring.  
* **Continual Learning:** Provides the trigger mechanism for when to retrain.

## **13. User Story: AI Essay Generation for Data Augmentation**

**Objective:** To generate high-quality AI essay samples using various language models to balance the training dataset and improve model robustness.

**Context:** The competition training data contains severe class imbalance with only 3 AI-generated essays versus 1,375 human essays. The `train_prompts.csv` file provides `instructions` and `source_text` for two essay prompts, encouraging participants to generate additional AI samples. Creating a diverse collection of AI essays from different models and generation parameters will balance the dataset and help build a more robust detection system.

**Acceptance Criteria:**
* A generation pipeline is created that uses the `instructions` and `source_text` from `train_prompts.csv` to create essay prompts.
* Multiple language models are integrated for essay generation:
  * OpenAI models (GPT-4, GPT-4-turbo, GPT-3.5-turbo)
  * Anthropic models (Claude 3.5 Sonnet, Claude 3 Haiku)  
  * Google models (Gemini Pro, Gemini Flash)
  * Open-source models (Llama 3, Mistral, etc.)
* Generation parameters are varied to create diversity:
  * Temperature settings (0.3, 0.7, 1.0, 1.2)
  * Top-p values (0.8, 0.9, 0.95)
  * Different prompt engineering techniques
* Target generation: ~1,375 AI essays to match human essay count (split between both prompts).
* Generated essays include metadata: model name, version, temperature, top_p, prompt_id, generation timestamp.
* Data quality controls: minimum/maximum length validation, duplicate detection, format consistency.
* Generated essays are saved in the same format as `train_essays.csv` with `generated=1`.
* The expanded dataset is validated by re-running the EDA notebook to ensure realistic distributions.

**MLOps Competition Criteria Fulfilled:**
* **Data Engineering:** Addresses the core data challenge of class imbalance through systematic augmentation.
* **Reproducibility:** Scripted generation process with documented parameters and model versions.
* **Best Practices:** Quality controls and validation ensure generated data maintains integrity.

## **14. User Story: Scheduled Retraining & Continual Learning Flow**

**Objective:** To create a fully automated, scheduled pipeline that retrains and redeploys the model using fresh data.  

**Context:** To combat model drift and continuously improve, the model must be periodically retrained on new data. This entire process should be automated and triggered either on a schedule or by a drift detection alert.  

**Acceptance Criteria:**
* A Prefect flow is created that orchestrates the full end-to-end process:  
  1. Fetch the latest production data from BigQuery.  
  2. Combine it with the original training data.  
  3. Run the training and HPO pipeline.  
  4. Evaluate the new model against the currently deployed production model.  
* If the new model shows a significant performance improvement, it is promoted to the "production" stage in the MLflow Model Registry.  
* A webhook or a subsequent CI/CD job is triggered to automatically deploy the newly promoted model to GCP Cloud Run.  
* The entire flow is scheduled to run on a monthly basis or can be triggered by the monitoring alert.

**MLOps Competition Criteria Fulfilled:**
* **Workflow Orchestration:** An advanced, end-to-end automated workflow.  
* **Continual Learning:** A complete, closed-loop system for model improvement.  
* **Monitoring:** Closes the loop from monitoring back to retraining.