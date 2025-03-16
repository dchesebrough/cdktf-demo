#!/usr/bin/env python
import json
from constructs import Construct
from cdktf import App, TerraformStack
from cdktf_cdktf_provider_aws.s3_bucket import S3Bucket
from cdktf_cdktf_provider_aws.s3_bucket_acl import S3BucketAcl
from cdktf_cdktf_provider_aws.s3_object import S3Object
from cdktf_cdktf_provider_aws.s3_bucket_website_configuration import (
    S3BucketWebsiteConfiguration, 
    S3BucketWebsiteConfigurationIndexDocument
)
from cdktf_cdktf_provider_aws.s3_bucket_policy import S3BucketPolicy
from cdktf_cdktf_provider_aws.provider import AwsProvider
from website import get_index_contents
from cdktf_cdktf_provider_aws.route53_zone import Route53Zone
from cdktf_cdktf_provider_aws.route53_record import Route53Record
from cdktf_cdktf_provider_aws.cloudfront_distribution import (
    CloudfrontDistribution,
    CloudfrontDistributionOrigin,
    CloudfrontDistributionDefaultCacheBehavior,
    CloudfrontDistributionViewerCertificate
)

ACCESS_IP_ADDRESS = "45.85.144.101"
HOSTED_ZONE_ID = "Z2PLO0R34FK2M7"
DOMAIN_NAME = "cdktfdemo.boredhusky.net"
BUCKET_NAME = "aura-cdktf-demo-static-website"

class AuraStaticWebsiteStack(TerraformStack):
    def __init__(self, scope: Construct, id: str):
        super().__init__(scope, id)

        AwsProvider(self, "AWS", region="us-east-1")

        bucket = S3Bucket(self, 
            "AuraStaticWebsiteBucket",
            bucket=BUCKET_NAME,
            website={
                "index_document": "index.html"
            }
        )

        cloudfront_distribution = CloudfrontDistribution(self, "CloudfrontDistribution",
            enabled=True,
            origins=[CloudfrontDistributionOrigin(
                domain_name=bucket.bucket_regional_domain_name,
                origin_id="S3Origin"
            )],
            default_cache_behavior=CloudfrontDistributionDefaultCacheBehavior(
                allowed_methods=["GET", "HEAD"],
                cached_methods=["GET", "HEAD"],
                target_origin_id="S3Origin",
                viewer_protocol_policy="redirect-to-https"
            )
        )

        S3BucketWebsiteConfiguration(self,
            "AuraStaticWebsiteBucketWebsiteConfiguration",
            bucket=bucket,
            index_document=S3BucketWebsiteConfigurationIndexDocument(self, "IndexDocument", suffix="index.html")
        )

        bucket_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "AllowAccessFromSpecificIP",
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": "s3:GetObject",
                    "Resource": f"arn:aws:s3:::{bucket.bucket}/*",
                    "Condition": {
                        "StringEquals": {
                            "aws:Referer": cloudfront_distribution.arn
                        }
                    }
                }
            ]
        }

        S3BucketPolicy(self, "BucketPolicy",
            bucket=bucket.bucket,
            policy=json.dumps(bucket_policy)
        )

        S3Object(self, "IndexHtml",
            bucket=bucket.bucket,
            key="index.html",
            content=get_index_contents(),
            content_type="text/html"
        )

        # CloudfrontDistributionCacheBehavior(self, "CloudfrontCacheInvalidation",
        #     distribution_id=cloudfront_distribution.id,
        #     paths=["/*"]
        # )

        Route53Record(self, "SubdomainRecord",
            zone_id=HOSTED_ZONE_ID,
            name=DOMAIN_NAME,
            type="CNAME",
            ttl=60,
            records=[bucket.website_endpoint]
        )

app = App()
AuraStaticWebsiteStack(app, "cdktf-demo")

app.synth()
