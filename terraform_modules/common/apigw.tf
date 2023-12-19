resource "aws_apigatewayv2_api" "api" {
  name          = replace("${var.system_name}-api", "_", "-")
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_stage" "api" {
  api_id      = aws_apigatewayv2_api.api.id
  name        = "$default"
  auto_deploy = true
}

resource "aws_apigatewayv2_authorizer" "type_a" {
  api_id           = aws_apigatewayv2_api.api.id
  authorizer_type  = "JWT"
  name             = "type_a"
  identity_sources = ["$request.header.Authorization"]

  jwt_configuration {
    audience = ["test_a"]
    issuer   = "https://luciferous-handson.auth0.com/"
  }
}

resource "aws_apigatewayv2_authorizer" "type_b" {
  api_id           = aws_apigatewayv2_api.api.id
  authorizer_type  = "JWT"
  name             = "type_b"
  identity_sources = ["$request.header.Authorization"]

  jwt_configuration {
    audience = ["test_b"]
    issuer   = "https://luciferous-handson.auth0.com/"
  }
}

resource "aws_apigatewayv2_integration" "api" {
  api_id           = aws_apigatewayv2_api.api.id
  integration_type = "AWS_PROXY"
  integration_uri  = module.check_posts.function_arn
}

resource "terraform_data" "aaa" {
  input = aws_apigatewayv2_authorizer.type_b.id
}

resource "aws_apigatewayv2_route" "api" {
  api_id             = aws_apigatewayv2_api.api.id
  route_key          = "GET /api/test"
  target             = "integrations/${aws_apigatewayv2_integration.api.id}"
  authorization_type = "JWT"
  authorizer_id      = terraform_data.aaa.output

  lifecycle {
    replace_triggered_by = [terraform_data.aaa.output]
  }
}
