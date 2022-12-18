terraform {
  required_version = ">= 1.0"
  backend "local" {}  
  required_providers {
    google = {
      source  = "hashicorp/google"
    }
  }
}

provider "google" {
  project = var.project_id
  region = var.region
}

//Enable Required API services for the project
resource "google_project_service" "iamcredentials" {
  project                    = var.project_id
  service                    = "iamcredentials.googleapis.com"
  disable_dependent_services = true
}


resource "google_project_service" "composer_api" {
  provider = google
  project = var.project_id
  service = "composer.googleapis.com"
  disable_on_destroy = false
}


resource "google_service_account" "custom_service_account" {
  provider = google
  account_id   = "account id"
  display_name = "Custom Service Account"
}

resource "google_project_iam_member" "editor" {
  project = var.project_id
  role    = "roles/editor"
  member  = "serviceAccount:${google_service_account.custom_service_account.email}"
}
resource "google_project_iam_member" "storage_admin" {
  project = var.project_id
  role    = "roles/storage.admin"
  member  = "serviceAccount:${google_service_account.custom_service_account.email}"
}

resource "google_project_iam_member" "bigquery_admin" {
  project = var.project_id
  role    = "roles/bigquery.admin"
  member  = "serviceAccount:${google_service_account.custom_service_account.email}"
}

resource "google_project_iam_member" "dataproc_admin" {
  project = var.project_id
  role    = "roles/dataproc.admin"
  member  = "serviceAccount:${google_service_account.custom_service_account.email}"
}

resource "google_project_iam_member" "composer_worker" {
  project  = var.project_id
  role     = "roles/composer.worker"
  member   = format("serviceAccount:%s", google_service_account.custom_service_account.email)
}

resource "google_service_account_iam_member" "custom_service_account" {
  service_account_id = google_service_account.custom_service_account.name
  role = "roles/composer.ServiceAgentV2Ext"
  member = "serviceAccount:service-${var.project_number}@cloudcomposer-accounts.iam.gserviceaccount.com"
}

// Data Lake Bucket
resource "google_storage_bucket" "data-lake-bucket" {
  name          = "${local.data_lake_bucket}_${var.project_id}" 
  location      = var.region

  storage_class = var.storage_class
  uniform_bucket_level_access = true

  versioning {
    enabled     = true
  }

  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      age = 30  // days
    }
  }

  force_destroy = true
}

//DW
resource "google_bigquery_dataset" "dataset" {
  dataset_id = var.BQ_DATASET
  project    = var.project_id
  location   = var.region
}

resource "google_dataproc_cluster" "spark_cluster" {
  name   = "ntsa-spark-cluster"
  region = var.region

  cluster_config {

    staging_bucket = google_storage_bucket.data-lake-bucket.name

    gce_cluster_config {
      zone    = var.zone

      shielded_instance_config {
        enable_secure_boot = true
      }
    }

    master_config {
      num_instances = 1
      machine_type  = "n2-standard"
      disk_config {
        boot_disk_type    = "pd-ssd"
        boot_disk_size_gb = 60
      }
    }

    worker_config {
      num_instances = 1
      machine_type  = "n2-standard"
      disk_config {
        boot_disk_size_gb = 60
      }
    }

    software_config {
      image_version = "2.0-debian10"
      override_properties = {
        "dataproc:dataproc.allow.zero.workers" = "true"
      }
    }

  }

}


resource "google_composer_environment" "example_environment" {
  provider = google
  name = "example-environment"

  config {
    software_config {
      image_version = "composer-2.0.31-airflow-2.2.5"
    }

    node_config {
      service_account = google_service_account.custom_service_account.email
    }

  }
}