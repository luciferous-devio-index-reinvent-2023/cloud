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

resource "aws_lambda_permission" "error_notifier" {
  action        = "lambda:InvokeFunction"
  function_name = module.error_notifier.function_arn
  principal     = "logs.amazonaws.com"
}