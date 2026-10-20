resource "random_id" "suffix" {
  byte_length = 4
}

resource "aws_s3_bucket" "proyecto" {
  bucket = "miad-dsa-proyecto-${random_id.suffix.hex}"
}

resource "aws_s3_bucket_versioning" "proyecto" {
  bucket = aws_s3_bucket.proyecto.id

  versioning_configuration {
    status = "Enabled"
  }
}

output "bucket_name" {
  value = aws_s3_bucket.proyecto.bucket
}