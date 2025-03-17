#!/usr/bin/env python
import json
from constructs import Construct
from cdktf import (
    App,
    TerraformStack,
    TerraformVariable,
    TerraformOutput
)
from cdktf_cdktf_provider_aws.s3_bucket import S3Bucket
from cdktf_cdktf_provider_aws.s3_object import S3Object
from cdktf_cdktf_provider_aws.s3_bucket_policy import S3BucketPolicy
from cdktf_cdktf_provider_aws.provider import AwsProvider
from cdktf_cdktf_provider_aws.route53_record import Route53Record
from cdktf_cdktf_provider_aws.cloudfront_distribution import (
    CloudfrontDistribution,
    CloudfrontDistributionOrigin,
    CloudfrontDistributionDefaultCacheBehavior,
    CloudfrontDistributionViewerCertificate,
    CloudfrontDistributionRestrictions
)
from cdktf_cdktf_provider_aws.cloudfront_origin_access_control import CloudfrontOriginAccessControl
from cdktf_cdktf_provider_aws.wafv2_ip_set import Wafv2IpSet
from cdktf_cdktf_provider_aws.wafv2_web_acl import (
    Wafv2WebAcl,
    Wafv2WebAclDefaultAction,
    Wafv2WebAclDefaultActionBlock,
    Wafv2WebAclVisibilityConfig,
    Wafv2WebAclRule,
    Wafv2WebAclRuleVisibilityConfig,
    Wafv2WebAclRuleAction,
    Wafv2WebAclRuleActionAllow
)
from cdktf_cdktf_provider_aws.data_aws_acm_certificate import DataAwsAcmCertificate
from cdktf_cdktf_provider_aws.data_aws_route53_zone import DataAwsRoute53Zone
from website import get_index_contents

class AuraStaticWebsiteStack(TerraformStack):
    '''
    Simple CDKTF Stack for deploying a static website on AWS using an S3 bucket.
    A CloudFront distribution is created to serve the website.
    It will be routable only from the IP address specified, and only via HTTPS.
    '''
    def __init__(self, scope: Construct, id: str):
        super().__init__(scope, id)

        AwsProvider(self, "AWS", region="us-east-1")

        domain_name = TerraformVariable(self, "DomainName",
            type = "string",
            default = "boredhusky.com"
        )

        domain_prefix = TerraformVariable(self, "DomainPrefix",
            type = "string",
            default = "cdktfdemo"
        )

        access_ip_address = TerraformVariable(self, "AccessIpAddress",
            type = "string",
            default = "96.255.75.10"
        )

        hosted_zone = DataAwsRoute53Zone(self, "HostedZoneId",
            name=domain_name.string_value
        )

        acm_ssl_certificate=DataAwsAcmCertificate(self, "AcmCertificate",
            domain=domain_name.string_value,
            most_recent=True,
            statuses=["ISSUED"]
        )

        bucket_config = S3Bucket(self, 
            "AuraStaticWebsiteBucket",
            bucket=f"{domain_prefix.string_value}-static-contents"
        )

        waf_ip_set = Wafv2IpSet(self, "WafIpSet",
            name="AuraStaticWebsiteWafIpSet",
            addresses=[f"{access_ip_address.string_value}/32"],
            ip_address_version="IPV4",
            scope="CLOUDFRONT"
        )

        waf_web_acl = Wafv2WebAcl(self, "WafWebAcl",
            default_action=Wafv2WebAclDefaultAction(
                block=Wafv2WebAclDefaultActionBlock()
            ),
            rule=[
                Wafv2WebAclRule(
                    name="AllowOnlySpecifiedIpRule",
                    priority=1,
                    action=Wafv2WebAclRuleAction(allow=Wafv2WebAclRuleActionAllow()),
                    statement={
                        "ip_set_reference_statement": {
                            "arn": waf_ip_set.arn
                        }
                    },
                    visibility_config=Wafv2WebAclRuleVisibilityConfig(
                        cloudwatch_metrics_enabled=False,
                        metric_name="AuraStaticWafAclRuleGroupRuleMetric",
                        sampled_requests_enabled=False
                    )
                )
            ],
            visibility_config=Wafv2WebAclVisibilityConfig(
                cloudwatch_metrics_enabled=False,
                metric_name="AuraStaticWafAclMetric",
                sampled_requests_enabled=False
            ),
            scope="CLOUDFRONT"
        )

        origin_access_control = CloudfrontOriginAccessControl(self, "CloudfrontOriginAccessControl",
            name="S3OriginAccessControl",
            origin_access_control_origin_type="s3",
            signing_behavior="always",
            signing_protocol="sigv4"
        )

        cloudfront_distribution = CloudfrontDistribution(self, "CloudfrontDistribution",
            enabled=True,
            origin=[CloudfrontDistributionOrigin(
                domain_name=bucket_config.bucket_regional_domain_name,
                origin_id="S3Origin",
                origin_access_control_id=origin_access_control.id
            )],
            aliases=[f"{domain_prefix.string_value}.{domain_name.string_value}"],
            default_cache_behavior=CloudfrontDistributionDefaultCacheBehavior(
                allowed_methods=["GET", "HEAD"],
                cached_methods=["GET", "HEAD"],
                target_origin_id="S3Origin",
                viewer_protocol_policy="redirect-to-https",
                # Note: 10 seconds is a very low cache TTL, but we use it here for demo purposes
                min_ttl=0,
                default_ttl=10,
                max_ttl=10,
                forwarded_values={
                    "query_string": False,
                    "cookies": {
                        "forward": "none"
                    }
                }
            ),
            restrictions=CloudfrontDistributionRestrictions(
                geo_restriction={
                    "restriction_type": "none"
                }
            ),
            viewer_certificate=CloudfrontDistributionViewerCertificate(
                acm_certificate_arn=acm_ssl_certificate.arn,
                ssl_support_method="sni-only",
                minimum_protocol_version="TLSv1.2_2021"
            ),
            web_acl_id=waf_web_acl.arn,
            default_root_object="index.html"
        )

        bucket_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "DenyNonSecureTransport",
                    "Effect": "Deny",
                    "Principal": "*",
                    "Action": "s3:GetObject",
                    "Resource": f"arn:aws:s3:::{bucket_config.bucket}/*",
                    "Condition": {
                        "Bool": {
                            "aws:SecureTransport": "false"
                        }
                    }
                },
                {
                    "Sid": "AllowCloudFrontServicePrincipalReadOnly",
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "cloudfront.amazonaws.com"
                    },
                    "Action": "s3:GetObject",
                    "Resource": f"arn:aws:s3:::{bucket_config.bucket}/*",
                    "Condition": {
                        "StringEquals": {
                            "AWS:SourceArn": cloudfront_distribution.arn
                        }
                    }
                }
            ]
        }

        S3BucketPolicy(self, "BucketPolicy",
            bucket=bucket_config.bucket,
            policy=json.dumps(bucket_policy)
        )

        S3Object(self, "IndexHtml",
            bucket=bucket_config.bucket,
            key="index.html",
            content=get_index_contents(),
            content_type="text/html"
        )

        route53_record = Route53Record(self, "SubdomainRecord",
            zone_id=hosted_zone.id,
            name=domain_prefix.string_value,
            type="CNAME",
            ttl=60,
            records=[cloudfront_distribution.domain_name]
        )

        TerraformOutput(self, "WebsiteURL",
            value="https://%s"%(route53_record.fqdn),
            description="The site will be accessible at this URL only from IP %s"%(access_ip_address.string_value)
        )

app = App()
AuraStaticWebsiteStack(app, "cdktf-demo")

app.synth()
