# --- CLOUD SQL (POSTGRES) ---

resource "google_sql_database_instance" "postgres" {
  name             = "${var.app_name}-db"
  database_version = "POSTGRES_15"
  region           = var.region

  settings {
    tier = "db-f1-micro" # Smallest tier to keep costs low during dev
    
    ip_configuration {
      # Cloud Run connects via the Cloud SQL Auth Proxy over the
      # /cloudsql unix socket (see the cloud_sql_instance volume in
      # cloud_run.tf / ingestion.tf), which is authenticated through the
      # Cloud SQL Admin API + IAM rather than the IP allowlist below.
      # No authorized_networks entry is needed for that path, so the
      # instance keeps a public IP (required by the proxy) without also
      # allowing raw internet access to it.
      ipv4_enabled = true
    }
  }
  deletion_protection = false # Set to true for production!
}

resource "google_sql_database" "database" {
  name     = "rag_memory"
  instance = google_sql_database_instance.postgres.name
}

resource "random_password" "db_password" {
  length  = 24
  special = false
}

resource "google_sql_user" "users" {
  name     = "rag_admin"
  instance = google_sql_database_instance.postgres.name
  password = random_password.db_password.result
}
