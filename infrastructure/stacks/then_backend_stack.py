import os

import aws_cdk as cdk
from aws_cdk.aws_lambda import Function, Code, Runtime, Architecture


class ThenBackendStack(cdk.Stack):

    def __init__(self, scope, id, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        Function(
            self,
            "ThenBackend",
            runtime=Runtime.PROVIDED_AL2,
            architecture=Architecture.ARM_64,
            handler="bootstrap",
            code=Code.from_asset(path="../rust-runtime/target/lambda/then-backend"),
            function_name="ThenBackend",
            environment={
                "TIMESTAMP": os.getenv("TIMESTAMP")
            },
        )
