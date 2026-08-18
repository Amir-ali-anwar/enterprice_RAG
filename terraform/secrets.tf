# --- SECRET MANAGER ---
# Provider-issued credentials (Groq, Qdrant, Logfire, LangSmith) are declared
# here as empty secret containers only. Terraform never sees their plaintext
# value, so it never lands in a .tfvars file or in Terraform state.
#
# After `terraform apply`, populate each one from your own machine with:
#   printf '%s' 'the-real-value' | gcloud secrets versions add <secret-id> \
#     --project=<project_id> --data-file=-
#
# db-password is the exception: Cloud SQL user creation requires Terraform
# to know the password, so it's generated in-state via random_password
# (database.tf) rather than typed into any file.

resource "google_project_service" "secretmanager" {
  project            = var.project_id
  service            = "secretmanager.googleapis.com"
  disable_on_destroy = false
}

locals {
  provider_secret_ids = [
    "groq-api-key",
    "qdrant-api-key",
    "logfire-token",
    "langsmith-api-key",
  ]
}

resource "google_secret_manager_secret" "provider_secrets" {
  for_each  = toset(local.provider_secret_ids)
  project   = var.project_id
  secret_id = each.value

  replication {
    auto {}
  }

  depends_on = [google_project_service.secretmanager]
}

resource "google_secret_manager_secret" "db_password" {
  project   = var.project_id
  secret_id = "db-password"

  replication {
    auto {}
  }

  depends_on = [google_project_service.secretmanager]
}

resource "google_secret_manager_secret_version" "db_password" {
  secret      = google_secret_manager_secret.db_password.id
  secret_data = random_password.db_password.result
}

# --- ACCESS GRANTS ---
# Least-privilege: each service account can only read the secrets it
# actually needs, not every secret in the project.

resource "google_secret_manager_secret_iam_member" "backend_access" {
  for_each  = toset(["groq-api-key", "qdrant-api-key", "logfire-token", "langsmith-api-key"])
  project   = var.project_id
  secret_id = google_secret_manager_secret.provider_secrets[each.value].secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.backend_sa.email}"
}

resource "google_secret_manager_secret_iam_member" "backend_db_password_access" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.db_password.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.backend_sa.email}"
}

resource "google_secret_manager_secret_iam_member" "ui_access" {
  for_each  = toset(["logfire-token", "langsmith-api-key"])
  project   = var.project_id
  secret_id = google_secret_manager_secret.provider_secrets[each.value].secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.ui_sa.email}"
}

resource "google_secret_manager_secret_iam_member" "ingestion_access" {
  for_each  = toset(["qdrant-api-key", "logfire-token", "langsmith-api-key"])
  project   = var.project_id
  secret_id = google_secret_manager_secret.provider_secrets[each.value].secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.ingestion_sa.email}"
}
