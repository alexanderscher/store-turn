resource "aws_ecr_repository" "store_turn_apple_ecr" {
  name = "store-turn-apple-ecr"
}


data "aws_ecr_image" "store_turn_apple_ecr" {
  repository_name = aws_ecr_repository.store_turn_apple_ecr.name
  image_tag       = "latest"
}
