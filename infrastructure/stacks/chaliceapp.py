import os

import aws_cdk as cdk
from aws_cdk.aws_certificatemanager import Certificate, CertificateValidation
from aws_cdk.aws_route53 import HostedZone, CfnRecordSet, ZoneDelegationRecord

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
                hosted_zone_id=os.getenv("HOSTED_ZONE_ID"),
                zone_name=aphex_domain),
            ttl=cdk.Duration.minutes(1)  # TODO: should increase this value once everything works
        )

        acm_cert = Certificate(
            self,
            "ThenBackyardCertificate",
            domain_name=domain_name,
            validation=CertificateValidation.from_dns(hosted_zone)
        )

        chalice = Chalice(
            self,
            'ChaliceApp',
            source_dir=RUNTIME_SOURCE_DIR,
            stage_config={
                "api_gateway_endpoint_type": "EDGE",
                "api_gateway_custom_domain": {
                    "domain_name": domain_name,
                    "certificate_arn": acm_cert.certificate_arn,
                }
            }
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
