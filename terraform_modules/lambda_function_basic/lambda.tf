data "archive_file" "package" {
  type        = "zip"
  output_path = "function_${var.function_identifier}.zip"
  source_dir  = "${path.root}/src/handlers/${var.function_identifier}"
}

resource "aws_lambda_function" "function" {
  function_name    = replace("${var.system_name}-${var.function_identifier}", "_", "-")
  role             = var.role_arn
  runtime          = "python3.11"
  architectures    = ["arm64"]
  handler          = "${var.function_identifier}.${var.handler_function}"
  memory_size      = var.memory_size
  timeout          = var.timeout
  filename         = data.archive_file.package.output_path
  source_code_hash = data.archive_file.package.output_base64sha256

  layers = concat(var.layers, [
    "arn:aws:lambda:${var.region}:017000801446:layer:AWSLambdaPowertoolsPythonV2-Arm64:51"
  ])

  environment {
    variables = var.environment_variables
  }
}

resource "aws_lambda_alias" "alias" {
  function_name    = aws_lambda_function.function.function_name
  function_version = aws_lambda_function.function.version
  name             = var.alias_name
}