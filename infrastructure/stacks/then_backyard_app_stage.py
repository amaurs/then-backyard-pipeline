
import aws_cdk as cdk

from stacks.chaliceapp import ChaliceApp


class ThenBackyardAppStage(cdk.Stage):
    def __init__(self, scope, id, **kwargs):
        super().__init__(scope, id, **kwargs)
        ChaliceApp(scope, 'then-backyard-pipeline')
