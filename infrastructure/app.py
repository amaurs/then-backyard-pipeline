#!/usr/bin/env python3
import logging
import os

try:
    from aws_cdk import core as cdk
except ImportError:
    import aws_cdk as cdk
from stacks.chaliceapp import ChaliceApp
from aws_cdk import pipelines


class ThenBackyardAppStage(cdk.Stage):
    def __init__(self, scope, id, **kwargs):
        super().__init__(scope, id, **kwargs)
        ChaliceApp(app, 'then-backyard-pipeline')


class ThenPipelineBackyardStack(cdk.Stack):
    def __init__(self, scope, id, **kwargs):
        super().__init__(scope, id, **kwargs)

        pipeline = pipelines.CodePipeline(
            scope=scope,
            id="ThenPipelineBackyard",
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
                    'pip install -r requirements',
                ]
            ),

        )

        pipeline.add_stage(
            stage=ThenBackyardAppStage(scope=scope, id=id)
        )


app = cdk.App()

logging.info(f'ACCOUNT 👉🏽 {os.getenv("ACCOUNT")}')
logging.info(f'REGION 🌎 {os.getenv("REGION")}')

ThenPipelineBackyardStack(app, 'ThenPipelineBackyardStack');

app.synth()


