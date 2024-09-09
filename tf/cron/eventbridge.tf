resource "aws_scheduler_schedule" "store_turn_invoke_schedule" {
  name       = "store-turn-invoke-schedule"
  group_name = "default"

  flexible_time_window {
    mode = "OFF"
  }

  schedule_expression          = "cron(15 16 9 9 ? 2024)"
  schedule_expression_timezone = "America/Los_Angeles"
  # cron(mins hour day month ? year)
  # cron(05 21 7 9 ? 2024)
  target {
    arn      = "arn:aws:lambda:us-east-1:742736545134:function:store-turn-invoke"
    role_arn = aws_iam_role.store_turn_scheduler_role.arn
  }
}
