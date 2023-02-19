import os

import aws_cdk as cdk
from aws_cdk.pipelines import CodePipeline, ShellStep, CodePipelineSource
from constructs import Construct


class ThenBackyardPipelineStack(cdk.Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        pipeline = CodePipeline(self, "ThenBackyardPipeline",
                        pipeline_name="ThenBackyardPipeline",
                        synth=ShellStep("Synth",
                            input=CodePipelineSource.git_hub("amaurs/then-backyard-pipeline", "main"),
                            commands=["npm install -g aws-cdk",
                                "python -m pip install -r requirements.txt",
                                "cdk synth"]
                        )
                    )
