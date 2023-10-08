import os

import aws_cdk as cdk
from aws_cdk.aws_certificatemanager import Certificate, CertificateValidation
from aws_cdk.aws_route53 import HostedZone, CfnRecordSet, ZoneDelegationRecord
from aws_cdk.aws_s3 import Bucket, CorsRule, HttpMethods, BlockPublicAccess
from aws_cdk.aws_iam import PolicyStatement, Policy

from chalice.cdk import Chalice


RUNTIME_SOURCE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), os.pardir, 'runtime')


class ChaliceApp(cdk.Stack):

    def __init__(self, scope, id, **kwargs):
        super().__init__(scope, id, **kwargs)

        # Deployment of chalice custom domain on cdk is based on https://github.com/aws/chalice/issues/1728

        aphex_domain = "then.gallery"
        domain_name = f"if.{aphex_domain}"

        hosted_zone = HostedZone(
            self,
            "ThenBackyardHostedZone",
            zone_name=domain_name,

        )

        # Using a zone delegation record was taken from https://bahr.dev/2020/09/01/multiple-frontends/

        ZoneDelegationRecord(
            self,
            "ThenBackyardZoneDelegationRecord",
            record_name=domain_name,
            name_servers=hosted_zone.hosted_zone_name_servers,
            zone=HostedZone.from_hosted_zone_attributes(
                self, "ThenHostedZone",
                hosted_zone_id=os.getenv("THEN_HOSTED_ZONE_ID"),
                zone_name=aphex_domain),
            ttl=cdk.Duration.minutes(1)  # TODO: should increase this value once everything works
        )

        acm_cert = Certificate(
            self,
            "ThenBackyardCertificate",
            domain_name=domain_name,
            validation=CertificateValidation.from_dns(hosted_zone)
        )

        bucket = Bucket(
            self,
            "ThenBackyardBucket",
            bucket_name=domain_name,
            block_public_access=BlockPublicAccess.BLOCK_ALL,
            cors=[
                CorsRule(
                    allowed_headers=["*"],
                    allowed_methods=[HttpMethods.PUT, HttpMethods.POST, HttpMethods.GET, HttpMethods.DELETE],
                    allowed_origins=["*"]
                )
            ])

        api_version = "v0"

        chalice = Chalice(
            self,
            'ChaliceApp',
            source_dir=RUNTIME_SOURCE_DIR,
            stage_config={
                "api_gateway_endpoint_type": "EDGE",
                "api_gateway_custom_domain": {
                    "domain_name": domain_name,
                    "certificate_arn": acm_cert.certificate_arn,
                },
                "api_gateway_stage": api_version,
                "environment_variables": {
                    'S3_BUCKET_NAME': domain_name,
                    'JWT_SECRET_NAME': os.getenv("JWT_SECRET_NAME"),
                }
            }
        )

        getSecretPolicyStatement = PolicyStatement(
            actions=['secretsmanager:GetSecretValue'],
            resources=['arn:aws:secretsmanager:us-east-1:892700351551:secret:*'])

        chalice.get_role('DefaultRole').attach_inline_policy(
            policy=Policy(scope=self, id='GetSecretPolicy', statements=[getSecretPolicyStatement]))

        bucket.grant_read_write(
            chalice.get_role('DefaultRole')
        )

        custom_domain = chalice.get_resource("ApiGatewayCustomDomain")
        CfnRecordSet(
            self,
            "ThenBackyardAPISubdomain",
            hosted_zone_id=hosted_zone.hosted_zone_id,
            name=domain_name,
            type="A",
            alias_target=CfnRecordSet.AliasTargetProperty(
                dns_name=custom_domain.get_att("DistributionDomainName").to_string(),
                hosted_zone_id=custom_domain.get_att(
                    "DistributionHostedZoneId"
                ).to_string(),
                evaluate_target_health=False,
            ),
        )
