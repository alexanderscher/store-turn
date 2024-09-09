provider "aws" {
  region = "us-east-1"

}

terraform {
  backend "s3" {
    bucket = "store-turn-tf-state-bucket"
    key    = "cron/terraform.tfstate"
    region = "us-east-1"
  }
}
