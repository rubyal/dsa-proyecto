#terraform {
#  backend "s3" {
#    bucket         = "miad-dsa-tfstate-740579k"
#    key            = "miad-dsa/terraform.tfstate"
#    region         = "us-east-1"
#    dynamodb_table = "ruby-miad-dsa-tflock"
#    encrypt        = true
#  }
#}