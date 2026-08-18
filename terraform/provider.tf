# --- GCP PROVIDER ---
terraform {
    required_providers {
        google = {
            source  = "hashicorp/google"
            version = ">= 6.0"
        }
        null = {
            source = "hashicorp/null"
            version = ">= 3.0"
        }
        time = {
            source  = "hashicorp/time"
            version = "~> 0.9"
        }
        random = {
            source  = "hashicorp/random"
            version = "~> 3.6"
        }
    }
}

provider "google" {
    project = var.project_id
    region  = var.region
}