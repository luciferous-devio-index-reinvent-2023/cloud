resource "aws_cloudwatch_log_group" "function" {
  name = "/aws/lambda/${aws_lambda_function.function.function_name}"
}