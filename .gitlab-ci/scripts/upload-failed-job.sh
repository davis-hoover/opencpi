#!/bin/bash

set -e

echo "Job failed, uploading OpenCPI source tree ..."

s3_bucket=opencpi-ci-artifacts
s3_object="${CI_PIPELINE_ID}/${CI_JOB_ID}.tar"

# Upload source tree, prepending 'opencpi/' to every file
tar -cf - -C "${CI_PROJECT_DIR}" --transform 's,^,opencpi/,' . |
  aws s3 cp - "s3://${s3_bucket}/${s3_object}"
echo "OpenCPI source tree available at https://${s3_bucket}.s3.us-east-2.amazonaws.com/${s3_object}"

# Apply tag to use expiration policy for failed jobs
aws s3api put-object-tagging --bucket "${s3_bucket}" --key "${s3_object}" --tagging 'TagSet=[{Key=type,Value=failed-job}]'
expires="$(aws --output yaml s3api head-object --bucket "${s3_bucket}" --key "${s3_object}" |
  awk -F\" '/Expiration:/ {print $2}')"
echo "Expires on ${expires}"

exit 0
