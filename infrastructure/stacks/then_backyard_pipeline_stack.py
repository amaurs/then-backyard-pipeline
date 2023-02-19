import os

import aws_cdk as cdk
from aws_cdk import pipelines
from constructs import Construct


class ThenBackyardPipelineStack(cdk.Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        pipeline = pipelines.CodePipeline(
            scope=scope,
            id="Pipeline",
            pipeline_name="ThenPipelineBackyard",
            synth=pipelines.ShellStep(
                'Build',
                input=pipelines.CodePipelineSource.git_hub(
                    repo_string='amaurs/then-backyard',
                    branch='master',
                    authentication=cdk.SecretValue.secrets_manager(
                        os.getenv('GITHUB_PERSONAL_ACCESS_TOKEN_SECRET_NAME'))),
                additional_inputs={
                    "multi-arm-bandits": pipelines.CodePipelineSource.git_hub(
                        repo_string='amaurs/then-backyard',
                        branch='master',
                        authentication=cdk.SecretValue.secrets_manager(
                            os.getenv('GITHUB_PERSONAL_ACCESS_TOKEN_SECRET_NAME')))},
                env={},
                primary_output_directory='cdk.out',
                commands=[
                    'ls',
                    "npm install -g aws-cdk",
                    'pip install -r requirements',
                ]
            ),

        )
