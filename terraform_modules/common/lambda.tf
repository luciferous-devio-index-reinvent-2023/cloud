data "archive_file" "lambda" {
  output_path = "lambda.zip"
  type        = "zip"
  source_dir  = "${path.root}/src"
}

module "error_notifier" {
  source = "../lambda_function_basic"

  function_identifier = "error_notifier"
  handler             = "handlers/error_notifier.handler"

  system_name      = var.system_name
  region           = var.region
  role_arn         = aws_iam_role.lambda.arn
  filename         = data.archive_file.lambda.output_path
  source_code_hash = data.archive_file.lambda.output_base64sha256
}

resource "aws_lambda_permission" "error_notifier" {
  action        = "lambda:InvokeFunction"
  function_name = module.error_notifier.function_arn
  principal     = "logs.amazonaws.com"
}