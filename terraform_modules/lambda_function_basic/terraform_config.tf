terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.26"
    }
  }
}

variable "system_name" {
  type     = string
  nullable = false
}

variable "function_identifier" {
  type     = string
  nullable = false
}

variable "role_arn" {
  type     = string
  nullable = false
}

variable "region" {
  type     = string
  nullable = false
}

variable "environment_variables" {
  type     = map(string)
  nullable = true
  default  = {}
}

variable "alias_name" {
  type     = string
  nullable = false
  default  = "process"
}

variable "memory_size" {
  type     = number
  nullable = false
  default  = 256
}

variable "timeout" {
  type     = number
  nullable = false
  default  = 120
}

variable "handler" {
  type     = string
  nullable = false
  default  = "handler"
}

variable "layers" {
  type     = list(string)
  nullable = false
  default  = []
}

output "function_name" {
  value = aws_lambda_function.function.function_name
}

output "function_arn" {
  value = aws_lambda_function.function.arn
}

output "function_alias_name" {
  value = aws_lambda_alias.alias.name
}

output "function_alias_arn" {
  value = aws_lambda_alias.alias.arn
}

output "log_group_name" {
  value = aws_cloudwatch_log_group.function.name
}