data "archive_file" "lambda" {
  output_path = "lambda.zip"
  type        = "zip"
  source_dir  = "${path.root}/src"
}

data "archive_file" "common_layer" {
  output_path = "layer_common.zip"
  type        = "zip"
  source_dir  = "${path.root}/src/layers/common"
}

resource "aws_lambda_layer_version" "common" {
  layer_name       = replace("${var.system_name}-common", "_", "-")
  filename         = data.archive_file.common_layer.output_path
  source_code_hash = data.archive_file.common_layer.output_base64sha256
}

module "error_notifier" {
  source = "../lambda_function_basic"

  function_identifier = "error_notifier"

  environment_variables = {
    SNS_TOPIC_ERROR = aws_sns_topic.error_topic.arn
  }

  layers      = [aws_lambda_layer_version.common.arn]
  system_name = var.system_name
  region      = var.region
  role_arn    = aws_iam_role.lambda.arn
}

resource "aws_cloudwatch_metric_alarm" "error_notifier" {
  alarm_name          = module.error_notifier.function_name
  alarm_actions       = [aws_sns_topic.error_topic.arn]
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  datapoints_to_alarm = 1
  dimensions = {
    FunctionName = module.error_notifier.function_name
  }
  metric_name        = "Errors"
  namespace          = "AWS/Lambda"
  period             = 60
  statistic          = "Sum"
  treat_missing_data = "notBreaching"
}

resource "aws_lambda_permission" "error_notifier" {
  action        = "lambda:InvokeFunction"
  function_name = module.error_notifier.function_arn
  qualifier     = module.error_notifier.function_alias_name
  principal     = "logs.amazonaws.com"
}

module "check_posts" {
  source = "../lambda_function"

  function_identifier = "check_posts"
  memory_size         = 512
  timeout             = 900

  environment_variables = {
    NOTION_DATABASE_ID                        = var.notion_database_id
    SSM_PARAM_NAME_NOTION_TOKEN               = aws_ssm_parameter.notion_token.name
    SSM_PARAM_NAME_CLOUDFLARE_DEPLOY_HOOK_URL = aws_ssm_parameter.cloudflare_deploy_hook_url.name
    S3_BUCKET_DATA                            = aws_s3_bucket.data.id
    S3_KEY_AUTHORS                            = "authors.json.gz"
    S3_KEY_EDITED                             = "edited.json"
    SNS_TOPIC_ERROR                           = aws_sns_topic.error_topic.arn
  }

  layers                       = [aws_lambda_layer_version.common.arn]
  system_name                  = var.system_name
  region                       = var.region
  role_arn                     = aws_iam_role.lambda.arn
  subscription_destination_arn = module.error_notifier.function_alias_arn
}

resource "aws_cloudwatch_event_rule" "check_posts" {
  name_prefix         = "check-posts-"
  description         = module.check_posts.function_name
  state               = "ENABLED"
  schedule_expression = "cron(0 16 * * ? *)"
}

resource "aws_lambda_permission" "check_posts" {
  action        = "lambda:InvokeFunction"
  function_name = module.error_notifier.function_alias_arn
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.check_posts.arn
}

resource "aws_cloudwatch_event_target" "check_posts" {
  arn  = module.check_posts.function_alias_arn
  rule = aws_cloudwatch_event_rule.check_posts.name
}

