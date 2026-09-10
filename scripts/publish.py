"""Publish the generated run report to S3 as a static site, using boto3.

    python scripts/publish.py <bucket-name> [region]

Does the same job as ``publish.sh`` without needing the AWS CLI installed.
``boto3`` is already a dependency of the pipeline, and the AWS CLI is a
separate installation that this project otherwise never asks for -- which is a
dependency a judge discovers only when the publish step fails. Same
credentials either way: whatever ``~/.aws/credentials`` holds.

The published page is one self-contained HTML file with no external requests,
so static hosting is all it needs -- no CloudFront, no build step, nothing left
running. There is no input surface on it, so there is nothing for a stranger to
abuse and no inference for them to spend your credits on.

Two URLs come out of this. Prefer the **HTTPS** one for anything you submit:
S3's website endpoint is HTTP-only, and a judge following an ``http://`` link
may meet a browser warning before they meet your project.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

ROOT = Path(__file__).resolve().parent.parent


def main(argv: list[str]) -> int:
    if not argv:
        print("\nusage: python scripts/publish.py <bucket-name> [region]",
              file=sys.stderr)
        return 64

    bucket = argv[0]
    region = argv[1] if len(argv) > 1 else "us-east-1"
    report = ROOT / "out" / "report.html"

    if not report.exists():
        print(f"No report at {report}.", file=sys.stderr)
        print("Generate one first:", file=sys.stderr)
        print("    python demo/run_demo.py --html --show-raw", file=sys.stderr)
        return 66

    html = report.read_text(encoding="utf-8")

    # Refuse to publish a page that says it was produced with stubbed models.
    # Sharing offline output as though it were the agent working would
    # misrepresent the project. See demo/offline.py.
    if "OFFLINE MODE" in html:
        print(f"Refusing to publish: {report} was generated with --offline.",
              file=sys.stderr)
        print("The judgment in it came from a hard-coded rule, not a model.",
              file=sys.stderr)
        return 65

    s3 = boto3.Session().client("s3", region_name=region)
    print(f"Publishing {report.name} ({len(html):,} bytes) to s3://{bucket} ({region})")

    try:
        s3.head_bucket(Bucket=bucket)
        print("  bucket exists")
    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code == "404":
            print("  creating bucket...")
            if region == "us-east-1":
                # us-east-1 is the API's default and rejects an explicit
                # LocationConstraint naming it.
                s3.create_bucket(Bucket=bucket)
            else:
                s3.create_bucket(
                    Bucket=bucket,
                    CreateBucketConfiguration={"LocationConstraint": region},
                )
        elif code == "403":
            print(f"  '{bucket}' belongs to another AWS account -- bucket names "
                  f"are globally unique. Choose another.", file=sys.stderr)
            return 1
        else:
            raise

    # Static website hosting needs public reads, which means clearing the
    # account-level block first. This bucket holds one generated HTML page
    # built from demonstration data -- do not reuse it for anything else.
    s3.put_public_access_block(
        Bucket=bucket,
        PublicAccessBlockConfiguration={
            "BlockPublicAcls": False, "IgnorePublicAcls": False,
            "BlockPublicPolicy": False, "RestrictPublicBuckets": False,
        },
    )

    policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Sid": "PublicReadForStaticSite",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": f"arn:aws:s3:::{bucket}/*",
        }],
    }
    # Clearing the block is not instant, and a policy set before it lands is
    # refused as though it were the policy that was wrong.
    for attempt in range(6):
        try:
            s3.put_bucket_policy(Bucket=bucket, Policy=json.dumps(policy))
            break
        except ClientError as e:
            if attempt == 5:
                raise
            print(f"  waiting for public-access change to land "
                  f"({e.response['Error']['Code']})...")
            time.sleep(3)
    print("  public-read policy applied")

    s3.put_bucket_website(
        Bucket=bucket,
        WebsiteConfiguration={"IndexDocument": {"Suffix": "index.html"}},
    )

    s3.put_object(
        Bucket=bucket, Key="index.html", Body=html.encode("utf-8"),
        ContentType="text/html; charset=utf-8",
        CacheControl="public, max-age=300",
    )
    print("  uploaded as index.html")

    print(f"\n  https://{bucket}.s3.{region}.amazonaws.com/index.html")
    print(f"  http://{bucket}.s3-website-{region}.amazonaws.com  (HTTP only)")
    print("\n  For the submission: say plainly that the page is generated from")
    print("  the demonstration dataset. It is real pipeline output, but the")
    print("  reports behind it are authored fixtures, not real residents'.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
