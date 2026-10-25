resource "random_id" "suffix" {
  byte_length = 4
}

data "aws_caller_identity" "current" {}

locals {
  equipo_account_ids = ["647432143535", "835600648116"]
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

resource "aws_s3_bucket_policy" "proyecto" {
  bucket = aws_s3_bucket.proyecto.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AdminCuentaCompleta"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action = "s3:*"
        Resource = [
          aws_s3_bucket.proyecto.arn,
          "${aws_s3_bucket.proyecto.arn}/*"
        ]
      },
      {
        Sid    = "EquipoListarBucket"
        Effect = "Allow"
        Principal = {
          AWS = [for id in local.equipo_account_ids : "arn:aws:iam::${id}:root"]
        }
        Action = [
          "s3:ListBucket",
          "s3:GetBucketLocation"
        ]
        Resource = aws_s3_bucket.proyecto.arn
      },
      {
        Sid    = "EquipoLeerEscribirObjetos"
        Effect = "Allow"
        Principal = {
          AWS = [for id in local.equipo_account_ids : "arn:aws:iam::${id}:root"]
        }
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = "${aws_s3_bucket.proyecto.arn}/*"
      }
    ]
  })
}

output "bucket_name" {
  value = aws_s3_bucket.proyecto.bucket
}
