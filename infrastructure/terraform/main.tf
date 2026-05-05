# This is our declarative entry point. 
# Later, we will specify if our provider is 'aws' or 'google' here.

terraform {
  required_version = ">= 1.0.0"
}

# Example placeholder for a Kubernetes cluster module
# module "kubernetes_cluster" {
#   source = "./modules/k8s"
# }
