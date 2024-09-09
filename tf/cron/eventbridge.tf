resource "aws_scheduler_schedule" "store_turn_invoke_schedule" {
  name       = "store-turn-invoke-schedule"
  group_name = "default"

  flexible_time_window {
    mode = "OFF"
  }

  schedule_expression          = "cron(20 14 9 9 ? 2024)"
  schedule_expression_timezone = "America/Los_Angeles"
  # cron(mins hour day month ? year)
  # cron(05 21 7 9 ? 2024)
  target {
    arn      = aws_lambda_function.store_turn_invoke.arn
    role_arn = aws_iam_role.store_turn_scheduler_role.arn
  }
}
