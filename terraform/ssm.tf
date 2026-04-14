resource "aws_ssm_parameter" "openai_api_key" {
  name        = "/adforge/OPENAI_API_KEY"
  description = "OpenAI API key for AdForge"
  type        = "SecureString"
  value       = var.openai_api_key

  tags = {
    App  = var.app_name
    Env  = var.environment
  }
}

resource "aws_ssm_parameter" "anthropic_api_key" {
  name        = "/adforge/ANTHROPIC_API_KEY"
  description = "Anthropic API key for AdForge"
  type        = "SecureString"
  value       = var.anthropic_api_key

  tags = {
    App  = var.app_name
    Env  = var.environment
  }
}
