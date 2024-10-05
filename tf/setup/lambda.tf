
data "archive_file" "lambda" {
  type        = "zip"
  source_dir  = "${path.module}/../../spotify/package"
  output_path = "${path.module}/../../zip/spotify_lambda.zip"
}

data "archive_file" "store_turn_lambda_invoke" {
  type        = "zip"
  source_file = "${path.module}/../../run/main.py"
  output_path = "${path.module}/../../zip/invoke_lambda.zip"

}

resource "aws_lambda_function" "store_turn_spotify" {
  function_name    = "store-turn-spotify"
  role             = aws_iam_role.store_turn_role.arn
  handler          = "main.lambda_handler"
  runtime          = "python3.10"
  filename         = data.archive_file.lambda.output_path
  source_code_hash = data.archive_file.lambda.output_base64sha256
  timeout          = 480
  environment {
    variables = {
      SPOTIFY_CLIENT_ID     = var.spotify_client_id
      SPOTIFY_CLIENT_SECRET = var.spotify_client_secret
      SPOTIFY_USER_ID       = var.spotify_user_id
      aws_access_key_id     = var.aws_access_key_id
      aws_secret_access_key = var.aws_secret_access_key
      ALEX                  = var.alex
      ARI                   = var.ari
      LAURA                 = var.laura
    }
  }
}

resource "aws_lambda_function" "store_turn_apple" {
  function_name = "store-turn-apple"
  role          = aws_iam_role.store_turn_role.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.store_turn_apple_ecr.repository_url}:latest"
  timeout       = 480
  memory_size   = 2048

  environment {
    variables = {
      APPLE_TEAM_ID         = var.apple_team_id
      APPLE_KEY_ID          = var.apple_key_id
      APPLE_PRIVATE_KEY     = var.apple_private_key
      aws_access_key_id     = var.aws_access_key_id
      aws_secret_access_key = var.aws_secret_access_key
      ALEX                  = var.alex
      ARI                   = var.ari
      LAURA                 = var.laura
    }
  }

}
# Data source to get the latest image digest from ECR
resource "aws_lambda_function" "store_turn_invoke" {
  function_name    = "store-turn-invoke"
  role             = aws_iam_role.store_turn_invoke_role.arn
  handler          = "main.lambda_handler"
  runtime          = "python3.10"
  filename         = data.archive_file.store_turn_lambda_invoke.output_path
  source_code_hash = data.archive_file.store_turn_lambda_invoke.output_base64sha256
  timeout          = 200
  environment {
    variables = {
      ALEX = var.alex
    }
  }
}

