import os

import aws_cdk as cdk
from aws_cdk.aws_route53 import HostedZone, CfnRecordSet

from chalice.cdk import Chalice


RUNTIME_SOURCE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), os.pardir, 'runtime')


class ChaliceApp(cdk.Stack):

    def __init__(self, scope, id, **kwargs):
        super().__init__(scope, id, **kwargs)

        domain_name = os.environ["API_GATEWAY_CUSTOM_DOMAIN"]

        self.chalice = Chalice(
            self, 'ChaliceApp', source_dir=RUNTIME_SOURCE_DIR,
            stage_config={
                "api_gateway_endpoint_type": "REGIONAL",
                "api_gateway_custom_domain": {
                    "domain_name": domain_name,
                    "certificate_arn": os.getenv("CERTIFICATE_ARN"),
                }
            }
        )

        # The following approach is based off https://github.com/aws/chalice/issues/1728

        hosted_zone = HostedZone.from_hosted_zone_id(self, "ThenHostedZone", os.getenv("HOSTED_ZONE_ID"))

        custom_domain = self.chalice.get_resource("ApiGatewayCustomDomain")
        CfnRecordSet(
            self,
            "ThenBackyardAPISubdomain",
            hosted_zone_id=hosted_zone.hosted_zone_id,
            name=domain_name,
            type="A",
            alias_target=CfnRecordSet.AliasTargetProperty(
                dns_name=custom_domain.get_att("RegionalDomainName").to_string(),
                hosted_zone_id=custom_domain.get_att(
                    "RegionalHostedZoneId"
                ).to_string(),
                evaluate_target_health=False,
            ),
        )
