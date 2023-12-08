data "aws_iam_policy_document" "assume_role_policy_lambda" {
  statement {
    sid     = "LambdaAssumeRolePolicy"
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      identifiers = ["lambda.amazonaws.com"]
      type        = "Service"
    }
  }
}

resource "aws_iam_role" "lambda" {
  assume_role_policy = data.aws_iam_policy_document.assume_role_policy_lambda.json
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.lambda.name
}

data "aws_iam_policy_document" "lambda" {
  statement {
    sid    = "SsmGetParameter"
    effect = "Allow"
    actions = [
      "ssm:GetParameter",
      "ssm:GetParameters"
    ]
    resources = [
      aws_ssm_parameter.notion_token.arn,
      aws_ssm_parameter.cloudflare_deploy_hook_url.arn,
    ]
  }
  statement {
    sid       = "kmsDecrypt"
    effect    = "Allow"
    actions   = ["kms:Decrypt"]
    resources = ["*"]
  }
  statement {
    sid    = "S3Access"
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:ListBucket"
    ]
    resources = [
      aws_s3_bucket.data.arn,
      "${aws_s3_bucket.data.arn}/*"
    ]
  }
  statement {
    sid       = "SnsPublish"
    effect    = "Allow"
    actions   = ["sns:Publish"]
    resources = [aws_sns_topic.error_topic.arn]
  }
}

resource "aws_iam_role_policy" "lambda" {
  name   = "lambda_policy"
  policy = data.aws_iam_policy_document.lambda.json
  role   = aws_iam_role.lambda.id
}
