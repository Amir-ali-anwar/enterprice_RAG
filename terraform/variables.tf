variable "project_id" {
  description = "The GCP Project ID"
  type        = string
}

variable "region" {
  description = "The GCP region for services"
  type        = string
  default     = "us-central1"
}

variable "app_name" {
  description = "Base name for all resources"
  type        = string
  default     = "enterprise-rag"
}

variable "qdrant_url" {
  description = "Qdrant Cloud endpoint"
  type        = string
}

variable "langsmith_project" {
  type    = string
  default = "rag_scale_test"
}

variable "groq_model" {
  description = "Groq model id used by the planner/guardrails/responder"
  type        = string
  default     = "openai/gpt-oss-120b"
}

# groq_api_key, qdrant_api_key, db_password, logfire_token, and
# langsmith_api_key are intentionally NOT Terraform variables anymore.
# They're read from Secret Manager at runtime (see secrets.tf and the
# secret_key_ref env blocks in cloud_run.tf / ingestion.tf) so their
# plaintext values never need to touch a .tfvars file or Terraform state.

variable "doc_ai_processor_id" {
  description = "The Google Cloud Document AI Processor ID"
  type        = string
}
