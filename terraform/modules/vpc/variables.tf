variable "name" {
  description = "Prefix name for VPC resources"
  type        = string
}

variable "public_subnet_cidrs" {
  type = list(string)
}

variable "private_subnet_cidrs" {
  type = list(string)
}
