# IAM role for the scheduler to invoke Lambda
resource "aws_iam_role" "store_turn_scheduler_role" {
  name = "store-turn-scheduler-role"

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

resource "aws_iam_role_policy" "store_turn_scheduler_policy" {
  name = "store-turn-scheduler-policy"
  role = aws_iam_role.store_turn_scheduler_role.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect   = "Allow",
      Action   = "lambda:InvokeFunction",
      Resource = "arn:aws:lambda:us-east-1:742736545134:function:store-turn-invoke"
    }]
  })
}
