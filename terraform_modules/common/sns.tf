resource "aws_sns_topic" "error_topic" {
  name_prefix = "error_topic_"
  display_name = "error_topic"
}