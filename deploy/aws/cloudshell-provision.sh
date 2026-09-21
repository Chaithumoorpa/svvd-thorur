#!/usr/bin/env bash
# Provisions the EC2 instance, security group, Elastic IP, S3 bucket, and IAM
# role for svvdthorur.org — run this in AWS CloudShell (the ">_" icon in the
# top nav of the AWS Console), not on your own machine.
#
# It's a one-time bootstrap, not idempotent — re-running it creates duplicate
# resources. Review the variables below, then paste the whole script into
# CloudShell.
#
# After it finishes: copy the "SUMMARY" block it prints back into the chat,
# and download the .pem file from CloudShell (☰ menu top-right → Actions →
# Download file → path: /home/cloudshell-user/svvd-thorur-key.pem) — you'll
# need it to SSH into the instance later. CloudShell's $HOME persists between
# sessions but isn't a permanent backup, so save a copy locally too.

set -euo pipefail

# ---- variables you may want to change -------------------------------------
REGION="ap-south-1"                 # Mumbai — closest to India; change if you prefer another region
KEY_NAME="svvd-thorur-key"
SG_NAME="svvd-thorur-sg"
INSTANCE_NAME="svvd-thorur-prod"
ROLE_NAME="svvd-thorur-backend-role"
# -----------------------------------------------------------------------------

export AWS_DEFAULT_REGION="$REGION"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
BUCKET_NAME="svvd-thorur-gallery-${ACCOUNT_ID}"

echo "==> Region: $REGION   Account: $ACCOUNT_ID   Bucket: $BUCKET_NAME"

echo "==> Creating key pair (saved to ~/${KEY_NAME}.pem — download this before closing CloudShell)"
aws ec2 create-key-pair --key-name "$KEY_NAME" --query 'KeyMaterial' --output text > "$HOME/${KEY_NAME}.pem"
chmod 400 "$HOME/${KEY_NAME}.pem"

echo "==> Finding default VPC"
VPC_ID=$(aws ec2 describe-vpcs --filters "Name=isDefault,Values=true" --query 'Vpcs[0].VpcId' --output text)

echo "==> Creating security group"
SG_ID=$(aws ec2 create-security-group \
  --group-name "$SG_NAME" \
  --description "svvd-thorur: ssh + http + https" \
  --vpc-id "$VPC_ID" \
  --query 'GroupId' --output text)

# SSH left open to the internet for now since CloudShell's IP isn't your own
# machine's IP — narrow this later in the EC2 console (Security Groups ->
# this group -> Edit inbound rules -> restrict port 22 to your IP).
aws ec2 authorize-security-group-ingress --group-id "$SG_ID" --protocol tcp --port 22 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-id "$SG_ID" --protocol tcp --port 80 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-id "$SG_ID" --protocol tcp --port 443 --cidr 0.0.0.0/0

echo "==> Looking up latest Amazon Linux 2023 (arm64) AMI"
AMI_ID=$(aws ssm get-parameters \
  --names /aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-arm64 \
  --query 'Parameters[0].Value' --output text)

echo "==> Launching t4g.micro instance"
INSTANCE_ID=$(aws ec2 run-instances \
  --image-id "$AMI_ID" \
  --instance-type t4g.micro \
  --key-name "$KEY_NAME" \
  --security-group-ids "$SG_ID" \
  --block-device-mappings '[{"DeviceName":"/dev/xvda","Ebs":{"VolumeSize":30,"VolumeType":"gp3"}}]' \
  --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=${INSTANCE_NAME}}]" \
  --query 'Instances[0].InstanceId' --output text)

echo "==> Waiting for it to reach 'running' (~30-60s)"
aws ec2 wait instance-running --instance-ids "$INSTANCE_ID"

echo "==> Allocating and attaching an Elastic IP"
ALLOC_ID=$(aws ec2 allocate-address --domain vpc --query 'AllocationId' --output text)
aws ec2 associate-address --instance-id "$INSTANCE_ID" --allocation-id "$ALLOC_ID" > /dev/null
PUBLIC_IP=$(aws ec2 describe-addresses --allocation-ids "$ALLOC_ID" --query 'Addresses[0].PublicIp' --output text)

echo "==> Creating S3 bucket for gallery photos"
if [ "$REGION" = "us-east-1" ]; then
  aws s3api create-bucket --bucket "$BUCKET_NAME" --region "$REGION"
else
  aws s3api create-bucket --bucket "$BUCKET_NAME" --region "$REGION" \
    --create-bucket-configuration LocationConstraint="$REGION"
fi

aws s3api put-public-access-block --bucket "$BUCKET_NAME" --public-access-block-configuration \
  BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=false,RestrictPublicBuckets=false

cat > "$HOME/bucket-policy.json" <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGalleryPhotos",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::${BUCKET_NAME}/gallery/*"
    }
  ]
}
EOF
aws s3api put-bucket-policy --bucket "$BUCKET_NAME" --policy "file://$HOME/bucket-policy.json"

cat > "$HOME/cors.json" <<EOF
{
  "CORSRules": [
    {
      "AllowedOrigins": ["https://svvdthorur.org", "https://www.svvdthorur.org", "http://localhost:3000"],
      "AllowedMethods": ["POST", "GET"],
      "AllowedHeaders": ["*"],
      "ExposeHeaders": ["ETag"]
    }
  ]
}
EOF
aws s3api put-bucket-cors --bucket "$BUCKET_NAME" --cors-configuration "file://$HOME/cors.json"

echo "==> Creating IAM role for the backend (EC2 instance role, no static keys)"
cat > "$HOME/trust-policy.json" <<'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": { "Service": "ec2.amazonaws.com" },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
aws iam create-role --role-name "$ROLE_NAME" --assume-role-policy-document "file://$HOME/trust-policy.json" > /dev/null

cat > "$HOME/s3-upload-policy.json" <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "s3:PutObject",
      "Resource": "arn:aws:s3:::${BUCKET_NAME}/gallery/*"
    }
  ]
}
EOF
aws iam put-role-policy --role-name "$ROLE_NAME" --policy-name s3-gallery-upload --policy-document "file://$HOME/s3-upload-policy.json"

aws iam create-instance-profile --instance-profile-name "$ROLE_NAME" > /dev/null
aws iam add-role-to-instance-profile --instance-profile-name "$ROLE_NAME" --role-name "$ROLE_NAME"
echo "==> Waiting ~15s for IAM to propagate before attaching the instance profile"
sleep 15
aws ec2 associate-iam-instance-profile --instance-id "$INSTANCE_ID" \
  --iam-instance-profile "Name=${ROLE_NAME}" > /dev/null

echo ""
echo "================= SUMMARY (copy this whole block back) ================="
echo "Region:          $REGION"
echo "Instance ID:     $INSTANCE_ID"
echo "Elastic IP:      $PUBLIC_IP"
echo "Security group:  $SG_ID"
echo "S3 bucket:       $BUCKET_NAME"
echo "IAM role:        $ROLE_NAME"
echo "Key pair file:   ~/${KEY_NAME}.pem  (download this from CloudShell now)"
echo "==========================================================================="
