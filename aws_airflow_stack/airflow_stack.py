from datetime import datetime
from aws_cdk import (
    Stack,
    Duration,
    Tags,
    CfnOutput,
    aws_s3 as s3,
    aws_s3_deployment as s3_deployment,
    aws_iam as iam,
    aws_mwaa as mwaa,
)
from constructs import Construct


class AirFlowStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        subnet_ids: list,
        security_group_id: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        project = "aws-airflow-proj"
        dt_now = datetime.now().strftime("%Y%m%d%H%M")

        code_bucket = s3.Bucket(
            self,
            "CodeBucket",
            bucket_name=f"{project}-python-code",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
        )
        dag_code_s3_path = f"dags_{dt_now}"
        s3_deployment.BucketDeployment(
            self,
            "DeployAirflowCode",
            destination_bucket=code_bucket,
            sources=[s3_deployment.Source.asset("./airflow_dags")],
            destination_key_prefix=dag_code_s3_path,
            prune=False,
        )

        airflow_env_name = f"{project}-environment"

        airflow_env_role = iam.Role(
            self,
            "MWAAEnvExecutionRole",
            assumed_by=iam.CompositePrincipal(
                iam.ServicePrincipal("airflow.amazonaws.com"),
                iam.ServicePrincipal("airflow-env.amazonaws.com"),
            ),
            inline_policies={
                "AirflowAccess": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=["airflow:PublishMetrics"],
                            resources=[
                                f"arn:aws:airflow:{self.region}:{self.account}:environment/{airflow_env_name}"
                            ],
                        )
                    ]
                ),
                "LoggingAccess": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=["logs:*"],
                            resources=[
                                f"arn:aws:logs:{self.region}:{self.account}:log-group:airflow-{airflow_env_name}-*"
                            ],
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=["logs:DescribeLogGroups"],
                            resources=["*"],
                        ),
                    ]
                ),
                "S3Access": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=["s3:*"],
                            resources=[
                                code_bucket.bucket_arn,
                                f"{code_bucket.bucket_arn}/*",
                            ],
                        )
                    ]
                ),
            },
        )

        mwaa_logging_configuration_prop = mwaa.CfnEnvironment.ModuleLoggingConfigurationProperty(  # cloud_watch_log_group_arn="cloudWatchLogGroupArn",
            # cloud_watch_log_group_arn="cloudWatchLogGroupArn",
            enabled=True,
            log_level="INFO",
        )

        aws_airflow = mwaa.CfnEnvironment(
            self,
            "AirflowEnvironment",
            name=airflow_env_name,
            airflow_configuration_options={
                "core.load_default_connections": False,
                "core.load_examples": False,
                "webserver.dag_default_view": "tree",
                "webserver.dag_orientation": "TB",
            },
            source_bucket_arn=code_bucket.bucket_arn,
            dag_s3_path=dag_code_s3_path,
            environment_class="mw1.small",
            execution_role_arn=airflow_env_role.role_arn,
            max_workers=3,
            webserver_access_mode="PUBLIC_ONLY",
            logging_configuration=mwaa.CfnEnvironment.LoggingConfigurationProperty(
                dag_processing_logs=mwaa_logging_configuration_prop,
                scheduler_logs=mwaa_logging_configuration_prop,
                task_logs=mwaa_logging_configuration_prop,
                webserver_logs=mwaa_logging_configuration_prop,
                worker_logs=mwaa_logging_configuration_prop,
            ),
            network_configuration=mwaa.CfnEnvironment.NetworkConfigurationProperty(
                security_group_ids=[security_group_id],
                subnet_ids=subnet_ids,
            ),
            # plugins_s3_object_version="pluginsS3ObjectVersion",
            # plugins_s3_path="pluginsS3Path",
            # requirements_s3_object_version="requirementsS3ObjectVersion",
            # requirements_s3_path="requirementsS3Path",
        )
