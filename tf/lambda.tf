data "archive_file" "lambda" {
  type        = "zip"
  source_dir  = "${path.module}/../spotify"
  output_path = "${path.module}/../zip/spotify_lambda.zip"
}

data "archive_file" "lambda_invoke_store_turn" {
  type        = "zip"
  source_file = "${path.module}/../run/main.py"
  output_path = "${path.module}/../zip/invoke_lambda.zip"
}

resource "aws_lambda_function" "spotify_store_turn" {
  function_name    = "spotify-store-turn"
  role             = aws_iam_role.spotify_store_turn_role.arn
  handler          = "main.lambda_handler"
  runtime          = "python3.10"
  filename         = data.archive_file.lambda.output_path
  source_code_hash = data.archive_file.lambda.output_base64sha256
  timeout          = 480
  environment {
    variables = {
      SPOTIFY_CLIENT_ID_L2TK     = var.spotify_client_id
      SPOTIFY_CLIENT_SECRET_L2TK = var.spotify_client_secret
      SPOTIFY_USER_ID_L2TK       = var.spotify_user_id
      aws_access_key_id          = var.aws_access_key_id
      aws_secret_access_key      = var.aws_secret_access_key
    }
  }
}

resource "aws_lambda_function" "invoke_spotify_store_turn" {
  function_name    = "invoke-spotify-store-turn"
  role             = aws_iam_role.invoke_spotify_store_turn_role.arn
  handler          = "main.lambda_handler"
  runtime          = "python3.10"
  filename         = data.archive_file.lambda_invoke_store_turn.output_path
  source_code_hash = data.archive_file.lambda_invoke_store_turn.output_base64sha256
  timeout          = 200
}


# terraform init
# terraform validate
# terraform plan
# terraform apply
