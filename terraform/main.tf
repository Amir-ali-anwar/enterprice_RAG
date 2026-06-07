data "google_project" "current" {
	project_id = var.project_id
}

locals {
	compute_default_service_account = "${data.google_project.current.number}-compute@developer.gserviceaccount.com"
	cloud_build_service_account     = "${data.google_project.current.number}@cloudbuild.gserviceaccount.com"
}

# --- ARTIFACT REGISTRY ---
resource "google_artifact_registry_repository" "repo" {
	location      = var.region
	repository_id = "${var.app_name}-repo"
	description   = "Docker repository for ${var.app_name}"
	format        = "DOCKER"
}

# --- NETWORKING ---
resource "google_compute_network" "rag_vpc" {
	name                    = "${var.app_name}-vpc"
	auto_create_subnetworks = true
}

# --- STORAGE ---
resource "google_storage_bucket" "raw_data" {
	name                        = "${var.project_id}-${var.app_name}-raw"
	location                    = var.region
	uniform_bucket_level_access = true
	force_destroy               = true
}

resource "google_storage_bucket" "processed_data" {
	name                        = "${var.project_id}-${var.app_name}-processed"
	location                    = var.region
	uniform_bucket_level_access = true
	force_destroy               = true
}

# --- REDIS ---
resource "google_redis_instance" "cache" {
	name               = "${var.app_name}-cache"
	display_name       = "${var.app_name} cache"
	tier               = "BASIC"
	memory_size_gb     = 1
	region             = var.region
	redis_version      = "REDIS_7_0"
	authorized_network = google_compute_network.rag_vpc.id
}

# --- SERVICE ACCOUNTS / IAM ---
resource "google_service_account" "ingestion_sa" {
	account_id   = "${replace(var.app_name, "-", "")}-ingestion"
	display_name = "Ingestion Service Account"
}

resource "google_project_iam_member" "ingestion_roles" {
	for_each = toset([
		"roles/run.invoker",
		"roles/storage.objectAdmin",
		"roles/cloudsql.client",
		"roles/documentai.apiUser",
	])

	project = var.project_id
	role    = each.value
	member  = "serviceAccount:${google_service_account.ingestion_sa.email}"
}

resource "google_project_iam_member" "gcs_pubsub_publishing" {
	project = var.project_id
	role    = "roles/pubsub.publisher"
	member  = "serviceAccount:service-${data.google_project.current.number}@gs-project-accounts.iam.gserviceaccount.com"
}

resource "google_project_iam_member" "eventarc_service_agent" {
	project = var.project_id
	role    = "roles/eventarc.serviceAgent"
	member  = "serviceAccount:service-${data.google_project.current.number}@gcp-sa-eventarc.iam.gserviceaccount.com"
}

resource "google_project_iam_member" "compute_build_storage_access" {
	project = var.project_id
	role    = "roles/storage.objectViewer"
	member  = "serviceAccount:${local.compute_default_service_account}"
}

resource "google_project_iam_member" "compute_build_artifact_registry_writer" {
	project = var.project_id
	role    = "roles/artifactregistry.writer"
	member  = "serviceAccount:${local.compute_default_service_account}"
}

resource "google_project_iam_member" "cloudbuild_storage_access" {
	project = var.project_id
	role    = "roles/storage.objectViewer"
	member  = "serviceAccount:${local.cloud_build_service_account}"
}

resource "google_project_iam_member" "cloudbuild_artifact_registry_writer" {
	project = var.project_id
	role    = "roles/artifactregistry.writer"
	member  = "serviceAccount:${local.cloud_build_service_account}"
}
