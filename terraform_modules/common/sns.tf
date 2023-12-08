resource "aws_sns_topic" "error_topic" {
  name_prefix = "error_topic"
  display_name = "error_topic"
}