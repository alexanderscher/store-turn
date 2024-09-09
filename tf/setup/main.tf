provider "aws" {
  region     = "us-east-1"
  access_key = var.aws_access_key_id
  secret_key = var.aws_secret_access_key
}


terraform {
  backend "s3" {
    bucket = "store-turn-tf-state-bucket"
    key    = "store-turn/terraform.tfstate"
    region = "us-east-1"
  }
}
