# resource "aws_scheduler_schedule" "invoke_spotify_store_turn_schedule" {
#   name       = "invoke-spotify-store-turn-schedule"
#   group_name = "default"

#   flexible_time_window {
#     mode = "OFF"
#   }

#   schedule_expression          = "cron(08 22 7 9 ? 2024)"
#   schedule_expression_timezone = "America/Los_Angeles"
#   # cron(mins hour day month ? year)
#   # cron(05 21 7 9 ? 2024)
#   target {
#     arn      = aws_lambda_function.invoke_store_turn.arn
#     role_arn = aws_iam_role.scheduler_role.arn
#   }
# }
