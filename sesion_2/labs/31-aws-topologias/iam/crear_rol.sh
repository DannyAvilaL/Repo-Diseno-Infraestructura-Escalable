#!/usr/bin/env bash
# Crea el bucket del laboratorio y el rol de servicio que Bedrock asume en batch.
# Basado en las plantillas oficiales "Create a custom service role for batch inference".
# Uso: ./iam/crear_rol.sh <bucket> [region]
set -euo pipefail
BUCKET="${1:?Indique el nombre del bucket}"
REGION="${2:-us-east-1}"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ROL="bedrock-batch-pqrs"
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

if [ "$REGION" = "us-east-1" ]; then
  aws s3api create-bucket --bucket "$BUCKET" --region "$REGION"
else
  aws s3api create-bucket --bucket "$BUCKET" --region "$REGION" --create-bucket-configuration LocationConstraint="$REGION"
fi
aws s3api put-public-access-block --bucket "$BUCKET" \
  --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
aws s3api put-bucket-tagging --bucket "$BUCKET" --tagging 'TagSet=[{Key=curso,Value=llm-infra}]'

sed -e "s/<ACCOUNT_ID>/$ACCOUNT_ID/g" -e "s/<REGION>/$REGION/g" iam/trust-policy.json > "$TMP/trust.json"
sed -e "s/<ACCOUNT_ID>/$ACCOUNT_ID/g" -e "s/<BUCKET>/$BUCKET/g" iam/permissions-policy.json > "$TMP/perms.json"

aws iam create-role --role-name "$ROL" --assume-role-policy-document "file://$TMP/trust.json" \
  --tags Key=curso,Value=llm-infra >/dev/null
aws iam put-role-policy --role-name "$ROL" --policy-name s3-lote-pqrs --policy-document "file://$TMP/perms.json"
echo "AWS_BATCH_ROLE_ARN=arn:aws:iam::$ACCOUNT_ID:role/$ROL"
