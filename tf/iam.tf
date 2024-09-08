# IAM Role for store-turn Lambda
resource "aws_iam_role" "store_turn_role" {
  name = "store-turn-role"

  assume_role_policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : [{
      "Action" : "sts:AssumeRole",
      "Effect" : "Allow",
      "Principal" : {
        "Service" : "lambda.amazonaws.com"
      }
    }]
  })
}

# Policy for store-turn Lambda to send emails and create logs
resource "aws_iam_role_policy" "store_turn_policy" {
  name = "store-turn-policy"
  role = aws_iam_role.store_turn_role.id

  policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : [
      {
        "Effect" : "Allow",
        "Action" : "ses:SendEmail",
        "Resource" : "arn:aws:ses:us-east-1:742736545134:identity/*"
      },
      {
        "Effect" : "Allow",
        "Action" : [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        "Resource" : "*"
      }
    ]
  })
}

# IAM Role for invoke-store-turn Lambda
resource "aws_iam_role" "invoke_store_turn_role" {
  name = "invoke-store-turn-role"

  assume_role_policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : [{
      "Action" : "sts:AssumeRole",
      "Effect" : "Allow",
      "Principal" : {
        "Service" : "lambda.amazonaws.com"
      }
    }]
  })
}

# Policy for invoke-store-turn Lambda to invoke other Lambda functions
resource "aws_iam_role_policy" "invoke_store_turn_policy" {
  name = "invoke-store-turn-policy"
  role = aws_iam_role.invoke_store_turn_role.id
  policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : [
      {
        "Effect" : "Allow",
        "Action" : "lambda:InvokeFunction",
        "Resource" : "*"
      }
    ]
  })
}


# IAM role for the scheduler to invoke Lambda
resource "aws_iam_role" "scheduler_role" {
  name = "scheduler-invoke-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect = "Allow",
      Principal = {
        Service = "scheduler.amazonaws.com"
      },
      Action = "sts:AssumeRole"
    }]
  })
}
# IAM policy for the scheduler role to invoke the Lambda function

resource "aws_iam_role_policy" "scheduler_invoke_policy" {
  name = "scheduler-invoke-policy"
  role = aws_iam_role.scheduler_role.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect   = "Allow",
      Action   = "lambda:InvokeFunction",
      Resource = aws_lambda_function.invoke_store_turn.arn
    }]
  })
}
