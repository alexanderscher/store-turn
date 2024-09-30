# cron(mins hour day month ? year)
# cron(05 21 7 9 ? 2024)



# resource "aws_scheduler_schedule" "store_turn_invoke_schedule_1" {
#   name       = "store-turn-invoke-schedule-1"
#   group_name = "default"

#   flexible_time_window {
#     mode = "OFF"
#   }

#   schedule_expression          = "cron(03 21 19 9 ? 2024)"
#   schedule_expression_timezone = "America/Los_Angeles"

#   target {
#     arn      = "arn:aws:lambda:us-east-1:742736545134:function:store-turn-invoke"
#     role_arn = aws_iam_role.store_turn_scheduler_role.arn
#   }
# }

# resource "aws_scheduler_schedule" "store_turn_invoke_schedule_2" {
#   name       = "store-turn-invoke-schedule-2"
#   group_name = "default"

#   flexible_time_window {
#     mode = "OFF"
#   }

#   schedule_expression          = "cron(15 21 19 9 ? 2024)"
#   schedule_expression_timezone = "America/Los_Angeles"
#   target {
#     arn      = "arn:aws:lambda:us-east-1:742736545134:function:store-turn-invoke"
#     role_arn = aws_iam_role.store_turn_scheduler_role.arn
#   }
# }

# resource "aws_scheduler_schedule" "store_turn_invoke_schedule_3" {
#   name       = "store-turn-invoke-schedule-3"
#   group_name = "default"

#   flexible_time_window {
#     mode = "OFF"
#   }

#   schedule_expression          = "cron(30 21 19 9 ? 2024)"
#   schedule_expression_timezone = "America/Los_Angeles"
#   target {
#     arn      = "arn:aws:lambda:us-east-1:742736545134:function:store-turn-invoke"
#     role_arn = aws_iam_role.store_turn_scheduler_role.arn
#   }
# }

