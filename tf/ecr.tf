resource "aws_ecr_repository" "apple_st_ecr" {
  name = "apple-st-ecr"
}


data "aws_ecr_image" "apple_st_ecr" {
  repository_name = aws_ecr_repository.apple_st_ecr.name
  image_tag       = "latest"
}
