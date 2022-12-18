locals {
  data_lake_bucket = "terraform"
}

variable "project_id" {
  description = "Your GCP Project ID"
  default     = "default id"
  type        = string
}

variable "project_number" {
  description = "Your GCP Project number"
  default     = "0000000000"
  type        = string
}

variable "region" {
  description = "Region for GCP resources. Choose as per your location: https://cloud.google.com/about/locations"
  default     = "us-central1"
  type        = string
}

variable "zone" {
  description = "Region for GCP resources. Choose as per your location: https://cloud.google.com/about/locations"
  default     = "us-central1-a"
  type        = string
}


variable "storage_class" {
  description = "Storage class type for your bucket. Check official docs for more info."
  default = "STANDARD"
}

variable "BQ_DATASET" {
  description = "BigQuery Dataset that raw data (from GCS) will be written to"
  type = string
  default = "default"
}

variable "sa" {
  description = "Dataset that raw data (from GCS) will be written to"
  type = string
  default = "default@project_id.iam.gserviceaccount.com"
}
