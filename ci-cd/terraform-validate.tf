# =============================================================================
# AOF Contract Validation — Terraform Integration
#
# Runs the AOF Python validator as part of infrastructure provisioning.
# Use this to enforce that a valid agent ownership contract exists before
# provisioning the infrastructure that hosts the agent.
#
# Usage:
#   terraform init
#   terraform plan -var="contract_path=path/to/agent-contract.yaml"
#   terraform apply
# =============================================================================

terraform {
  required_providers {
    null = {
      source  = "hashicorp/null"
      version = "~> 3.0"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.0"
    }
  }
}

# ---------------------------------------------------------------------------
# Variables
# ---------------------------------------------------------------------------

variable "contract_path" {
  description = "Path to the AOF agent ownership contract YAML file to validate before provisioning."
  type        = string
}

variable "python_path" {
  description = "Path to the Python interpreter to use for validation."
  type        = string
  default     = "python3"
}

variable "validator_path" {
  description = "Path to the AOF validate-contract.py script."
  type        = string
  default     = "tools/validate-contract.py"
}

# ---------------------------------------------------------------------------
# Data source: load and verify the contract file exists
# ---------------------------------------------------------------------------

data "local_file" "agent_contract" {
  filename = var.contract_path
}

# ---------------------------------------------------------------------------
# Validation resource
# Runs the Python validator before any dependent resources are provisioned.
# If validation fails, Terraform apply is blocked.
# ---------------------------------------------------------------------------

resource "null_resource" "validate_aof_contract" {
  # Re-run validation whenever the contract file changes
  triggers = {
    contract_hash = data.local_file.agent_contract.content_md5
  }

  provisioner "local-exec" {
    command = "${var.python_path} ${var.validator_path} ${var.contract_path}"
    on_failure = fail  # Block provisioning if validation fails
  }
}

# ---------------------------------------------------------------------------
# Outputs
# ---------------------------------------------------------------------------

output "contract_validated" {
  description = "Whether the AOF contract passed validation (true = provisioning allowed)."
  value       = true
  depends_on  = [null_resource.validate_aof_contract]
}

output "contract_path" {
  description = "Path to the validated contract."
  value       = var.contract_path
}

output "contract_hash" {
  description = "MD5 hash of the contract file at time of validation."
  value       = data.local_file.agent_contract.content_md5
}
