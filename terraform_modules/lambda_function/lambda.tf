module "function" {
  source = "../lambda_function_basic"

  system_name           = var.system_name
  function_identifier   = var.function_identifier
  role_arn              = var.role_arn
  region                = var.region
  environment_variables = var.environment_variables
  alias_name            = var.alias_name
  memory_size           = var.memory_size
  timeout               = var.timeout
  handler               = var.handler
  layers                = var.layers
}

resource "aws_cloudwatch_log_subscription_filter" "error_log" {
  destination_arn = var.subscription_destination_arn
  filter_pattern  = "{ $.level = \"ERROR\" }"
  log_group_name  = module.function.log_group_name
  name            = "error-log"
}

resource "aws_cloudwatch_log_subscription_filter" "unexpected_exit" {
  destination_arn = var.subscription_destination_arn
  filter_pattern  = "?\"Task timed out\" ?\"Runtime exited with error\" ?\"Runtime.ImportModuleError\""
  log_group_name  = module.function.log_group_name
  name            = "unexpected-exit"
}
