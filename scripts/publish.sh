#!/usr/bin/env bash
# Publish the generated run report to S3 as a static site.
#
#   ./scripts/publish.sh my-bucket-name [aws-region]
#
# The page is one self-contained HTML file with no scripts and no external
# requests, so static website hosting is all it needs — no CloudFront, no
# build step, and nothing to keep running. Cost at demo traffic is pennies.
#
# There is no input surface here on purpose. The published page is read-only,
# so there is nothing to abuse and no inference for a stranger to spend your
# credits on. See IMPLEMENTATION_PLAN.md §2.

set -euo pipefail

BUCKET="${1:-}"
REGION="${2:-${AWS_REGION:-us-west-2}}"
REPORT="${FNA_HTML_OUT:-out/report.html}"

if [[ -z "$BUCKET" ]]; then
  echo "usage: $0 <bucket-name> [region]" >&2
  exit 64
fi

if [[ ! -f "$REPORT" ]]; then
  echo "No report at $REPORT." >&2
  echo "Generate one first:" >&2
  echo "    python demo/run_demo.py --html $REPORT" >&2
  exit 66
fi

# Refuse to publish a page that says it was produced with stubbed models.
# Recording or sharing offline output as though it were the agent working
# would misrepresent the project. See demo/offline.py.
if grep -q 'OFFLINE MODE' "$REPORT"; then
  echo "Refusing to publish: $REPORT was generated with --offline." >&2
  echo "The judgment in it came from a hard-coded rule, not from a model." >&2
  echo "Re-run without --offline before publishing." >&2
  exit 65
fi

echo "Publishing $REPORT to s3://$BUCKET ($REGION)"

if ! aws s3api head-bucket --bucket "$BUCKET" 2>/dev/null; then
  echo "Creating bucket..."
  if [[ "$REGION" == "us-east-1" ]]; then
    aws s3api create-bucket --bucket "$BUCKET" --region "$REGION"
  else
    aws s3api create-bucket --bucket "$BUCKET" --region "$REGION" \
      --create-bucket-configuration "LocationConstraint=$REGION"
  fi

  # Static website hosting needs public reads, which means clearing the
  # account-level block first. This bucket holds one generated HTML page
  # built from demonstration data — do not reuse it for anything else.
  aws s3api put-public-access-block --bucket "$BUCKET" \
    --public-access-block-configuration \
    "BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false"

  aws s3api put-bucket-policy --bucket "$BUCKET" --policy "$(cat <<POLICY
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "PublicReadForStaticSite",
    "Effect": "Allow",
    "Principal": "*",
    "Action": "s3:GetObject",
    "Resource": "arn:aws:s3:::$BUCKET/*"
  }]
}
POLICY
)"

  aws s3 website "s3://$BUCKET" --index-document index.html
fi

aws s3 cp "$REPORT" "s3://$BUCKET/index.html" \
  --content-type "text/html; charset=utf-8" \
  --cache-control "public, max-age=300"

echo
echo "  http://$BUCKET.s3-website.$REGION.amazonaws.com"
echo
echo "  Note for the submission: say plainly that the page is generated from"
echo "  the demonstration dataset. It is real pipeline output, but the reports"
echo "  behind it are authored fixtures, not reports from real residents."
