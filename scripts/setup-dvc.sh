#!/usr/bin/env bash
# ──────────────────────────────────────────────
# Configura el remote de DVC usando S3_BUCKET_NAME del .env
# Uso:  ./scripts/setup_dvc.sh
# ──────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Cargar .env si existe
ENV_FILE="$PROJECT_ROOT/.env"
if [ -f "$ENV_FILE" ]; then
  set -a
  source "$ENV_FILE"
  set +a
fi

# Validar que la variable exista
if [ -z "${S3_BUCKET_NAME:-}" ]; then
  echo "❌ Error: S3_BUCKET_NAME no está definida."
  echo "   Copia .env.example a .env y llena S3_BUCKET_NAME con el nombre del bucket."
  exit 1
fi

REGION="${AWS_DEFAULT_REGION:-us-east-1}"
REMOTE_URL="s3://${S3_BUCKET_NAME}/dvcstore"

echo "🔧 Configurando DVC remote..."
echo "   Bucket : ${S3_BUCKET_NAME}"
echo "   URL    : ${REMOTE_URL}"
echo "   Región : ${REGION}"

cd "$PROJECT_ROOT"
dvc remote modify aws-remote url "$REMOTE_URL"
dvc remote modify aws-remote region "$REGION"

echo "✅ DVC remote 'aws-remote' actualizado."
echo "   Verifica con: dvc remote list"
