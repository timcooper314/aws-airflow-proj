#!/usr/bin/env python3
import aws_cdk as cdk
from aws_airflow_stack.airflow_stack import AirFlowStack


app = cdk.App()
config = dict(app.node.try_get_context("StackParameters"))
env = cdk.Environment(
    account=config["AccountID"],
    region=config["Region"],
)
airflow_stack = AirFlowStack(
    app,
    "airflow-proj",
    env=env,
)
app.synth()
