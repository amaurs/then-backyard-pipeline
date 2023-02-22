import os

import aws_cdk as cdk
from aws_cdk.aws_certificatemanager import Certificate, CertificateValidation
from aws_cdk.aws_route53 import HostedZone, CfnRecordSet

from chalice.cdk import Chalice


RUNTIME_SOURCE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), os.pardir, 'runtime')


class ChaliceApp(cdk.Stack):

    def __init__(self, scope, id, **kwargs):
        super().__init__(scope, id, **kwargs)

        # The following approach is based off https://github.com/aws/chalice/issues/1728

        self.domain_name = "api.then.gallery"

        self.hosted_zone = HostedZone(
            self,
            "ThenHostedZone",
            zone_name=os.getenv("HOSTED_ZONE_ID"))

        self.acm_cert = Certificate(
            self,
            "ThenBackyardCertificate",
            domain_name=self.domain_name,
            validation=CertificateValidation.from_dns(self.hosted_zone))

        self.chalice = Chalice(
            self, 'ChaliceApp',
            source_dir=RUNTIME_SOURCE_DIR,
            stage_config={
                "api_gateway_endpoint_type": "EDGE",
                "api_gateway_custom_domain": {
                    "domain_name": self.domain_name,
                    "certificate_arn": self.acm_cert.certificate_arn,
                }
            })

        self.custom_domain = self.chalice.get_resource("ApiGatewayCustomDomain")
        CfnRecordSet(
            self,
            "ThenBackyardAPISubdomain",
            hosted_zone_id=self.hosted_zone.hosted_zone_id,
            name=self.domain_name,
            type="A",
            alias_target=CfnRecordSet.AliasTargetProperty(
                dns_name=self.custom_domain.get_att("DistributionDomainName").to_string(),
                hosted_zone_id=self.custom_domain.get_att(
                    "DistributionHostedZoneId"
                ).to_string(),
                evaluate_target_health=False,
            ),
        )
