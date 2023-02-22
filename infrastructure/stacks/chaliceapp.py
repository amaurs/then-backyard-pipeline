import os

import aws_cdk as cdk

from chalice.cdk import Chalice


RUNTIME_SOURCE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), os.pardir, 'runtime')


class ChaliceApp(cdk.Stack):

    def __init__(self, scope, id, **kwargs):
        super().__init__(scope, id, **kwargs)
        self.chalice = Chalice(
            self, 'ChaliceApp', source_dir=RUNTIME_SOURCE_DIR,
            stage_config={
                "stages": {
                    "dev": {
                        "api_gateway_custom_domain": {
                            "domain_name": os.getenv("API_GATEWAY_CUSTOM_DOMAIN"),
                            "certificate_arn": os.getenv("CERTIFICATE_ARN"),
                        }
                    }
                }
            }
        )
