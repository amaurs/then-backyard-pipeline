import os

import aws_cdk as cdk
from aws_cdk.pipelines import CodePipeline, ShellStep, CodePipelineSource
from constructs import Construct

from stacks.then_backyard_app_stage import ThenBackyardAppStage


class ThenBackyardPipelineStack(cdk.Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        pipeline = CodePipeline(self, "ThenBackyardPipeline",
                        pipeline_name="ThenBackyardPipeline",
                        synth=ShellStep("Synth",
                                        input=CodePipelineSource.git_hub(
                                            "amaurs/then-backyard-pipeline", "main",
                                            authentication=cdk.SecretValue.secrets_manager(
                                                os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN_SECRET_NAME"))),
                                        additional_inputs={
                                            'runtime': CodePipelineSource.git_hub(
                                                "amaurs/then-backyard", "main",
                                                authentication=cdk.SecretValue.secrets_manager(
                                                    os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN_SECRET_NAME"))),
                                        },
                                        commands=[
                                            "npm install -g aws-cdk",
                                            "python -m pip install -r requirements.txt",
                                            "ls",
                                            "ls infrastructure",
                                            "ls runtime",
                                            "cd runtime",
                                            "pytest",
                                            "cd ../infrastructure",
                                            "cdk synth"],
                                        env={
                                            'ACCOUNT': os.getenv("ACCOUNT"),
                                            'REGION': os.getenv("REGION"),
                                            'GITHUB_PERSONAL_ACCESS_TOKEN_SECRET_NAME': os.getenv(
                                                "GITHUB_PERSONAL_ACCESS_TOKEN_SECRET_NAME"),
                                            'THEN_HOSTED_ZONE_ID': os.getenv("THEN_HOSTED_ZONE_ID"),
                                        },
                                        primary_output_directory='infrastructure/cdk.out'
                                        )
                                )

        pipeline.add_stage(ThenBackyardAppStage(self, "Deployment",
                                                env=cdk.Environment(account=os.getenv("ACCOUNT"),
                                                                    region=os.getenv("REGION"))))
