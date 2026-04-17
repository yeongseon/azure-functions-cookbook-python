terraform {
  required_version = ">= 1.5.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.116"
    }
  }
}

provider "azurerm" {
  features {}
}

variable "base_name" {
  type    = string
  default = "signalrnotifications"
}

variable "location" {
  type    = string
  default = "eastus"
}

variable "resource_group_name" {
  type    = string
  default = "azure-functions-cookbook-rg"
}

locals {
  unique_suffix        = substr(md5("${var.base_name}-${var.resource_group_name}"), 0, 8)
  storage_account_name = substr(lower("st${replace(var.base_name, "-", "")}${local.unique_suffix}"), 0, 24)
  function_app_name    = "${var.base_name}-${substr(local.unique_suffix, 0, 6)}"
}

resource "azurerm_storage_account" "storage" {
  name                            = local.storage_account_name
  resource_group_name             = var.resource_group_name
  location                        = var.location
  account_tier                    = "Standard"
  account_replication_type        = "LRS"
  min_tls_version                 = "TLS1_2"
  allow_nested_items_to_be_public = false
}

resource "azurerm_service_plan" "plan" {
  name                = "${var.base_name}-plan"
  resource_group_name = var.resource_group_name
  location            = var.location
  os_type             = "Linux"
  sku_name            = "Y1"
}

resource "azurerm_signalr_service" "signalr" {
  name                = "${var.base_name}-signalr"
  resource_group_name = var.resource_group_name
  location            = var.location
  sku {
    name     = "Free_F1"
    capacity = 1
  }
  service_mode = "Serverless"
}
resource "azurerm_linux_function_app" "function_app" {
  name                       = local.function_app_name
  resource_group_name        = var.resource_group_name
  location                   = var.location
  service_plan_id            = azurerm_service_plan.plan.id
  storage_account_name       = azurerm_storage_account.storage.name
  storage_account_access_key = azurerm_storage_account.storage.primary_access_key
  https_only                 = true

  site_config {
    application_stack {
      python_version = "3.11"
    }
  }

  app_settings = {
    FUNCTIONS_EXTENSION_VERSION    = "~4"
    FUNCTIONS_WORKER_RUNTIME       = "python"
    SCM_DO_BUILD_DURING_DEPLOYMENT = "1"
    AzureWebJobsStorage            = azurerm_storage_account.storage.primary_connection_string
    AzureSignalRConnectionString    = "Endpoint=https://${var.base_name}-signalr.service.signalr.net;AccessKey=replace-me;Version=1.0;"
    SIGNALR_HUB_NAME                = "notifications"
  }
}
