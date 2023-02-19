#!/usr/bin/env python3
import logging
import os

from stacks.then_backyard_pipeline_stack import ThenBackyardPipelineStack

import aws_cdk as cdk

logging.info(f'ACCOUNT 👉🏽 {os.getenv("ACCOUNT")}')
logging.info(f'REGION 🌎 {os.getenv("REGION")}')

app = cdk.App()
ThenBackyardPipelineStack(
    scope=app,
    id='ThenPipelineBackyardStack',
    env=cdk.Environment(account=os.getenv("ACCOUNT"), region=os.getenv("REGION")))

app.synth()
