from aws_cdk import (
    Stack,
    Duration,
    Tags,
    CfnOutput,
)
from constructs import Construct


class AirFlowStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # TODO: Create airflow resources
        pass
