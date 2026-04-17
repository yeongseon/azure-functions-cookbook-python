terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
}

variable "base_name" {
  type = string
}

variable "location" {
  type    = string
  default = "eastus"
}

locals {
  storage_account_name = substr("${replace(lower(var.base_name), "-", "")}store", 0, 24)
}

resource "azurerm_resource_group" "rg" {
  name     = "${var.base_name}-rg"
  location = var.location
}

resource "azurerm_storage_account" "sa" {
  name                     = local.storage_account_name
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  min_tls_version          = "TLS1_2"
  allow_nested_items_to_be_public = false
}

resource "azurerm_storage_container" "events" {
  name                  = "events"
  storage_account_name  = azurerm_storage_account.sa.name
  container_access_type = "private"
}

resource "azurerm_storage_queue" "eventgrid" {
  name                 = "eventgrid-events"
  storage_account_name = azurerm_storage_account.sa.name
}

resource "azurerm_eventgrid_topic" "topic" {
  name                = "${var.base_name}-topic"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  input_schema        = "EventGridSchema"
}

resource "azurerm_eventgrid_event_subscription" "subscription" {
  name  = "${var.base_name}-subscription"
  scope = azurerm_eventgrid_topic.topic.id

  storage_queue_endpoint {
    storage_account_id = azurerm_storage_account.sa.id
    queue_name         = azurerm_storage_queue.eventgrid.name
  }
}

resource "azurerm_service_plan" "plan" {
  name                = "${var.base_name}-plan"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  os_type             = "Linux"
  sku_name            = "Y1"
}

resource "azurerm_linux_function_app" "func" {
  name                       = var.base_name
  resource_group_name        = azurerm_resource_group.rg.name
  location                   = azurerm_resource_group.rg.location
  service_plan_id            = azurerm_service_plan.plan.id
  storage_account_name       = azurerm_storage_account.sa.name
  storage_account_access_key = azurerm_storage_account.sa.primary_access_key
  https_only                 = true

  site_config {
    application_stack {
      python_version = "3.11"
    }
  }

  app_settings = {
    FUNCTIONS_EXTENSION_VERSION   = "~4"
    FUNCTIONS_WORKER_RUNTIME      = "python"
    SCM_DO_BUILD_DURING_DEPLOYMENT = "1"
  }
}
