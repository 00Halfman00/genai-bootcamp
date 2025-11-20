from aws_cdk import RemovalPolicy, Duration
from aws_cdk.aws_s3 import Bucket
from constructs import Construct
import aws_cdk.aws_dynamodb as dynamodb
import aws_cdk.aws_lambda as _lambda
import aws_cdk.aws_events as events
import aws_cdk.aws_events_targets as targets
import aws_cdk.aws_logs as logs

from .cognito import Cognito
from .apifn import ApiFn


class Admin(Construct):
    dynamodb_table: dynamodb.TableV2
    endpoint: str
    domain_name: str
    user_pool_id: str
    user_pool_client_id: str


    def __init__(self, scope: Construct, id: str,
                   kb_id: str,  # Bedrock Knowledge Base ID
                   kb_data_src_id: str,  # Bedrock Knowledge Base Data Source ID
                   kb_input_bucket: Bucket, # S3 Bucket for input documents
                 ) -> None:
        super().__init__(scope, id)

        # Database used to store settings, pending questions etc
        self.dynamodb_table = dynamodb.TableV2(self, 'AdminTable',
                                          partition_key=dynamodb.Attribute(name='PK', type=dynamodb.AttributeType.STRING),
                                          sort_key=dynamodb.Attribute(name='SK', type=dynamodb.AttributeType.STRING),
                                          removal_policy=RemovalPolicy.DESTROY,
                                        )

        cognito = Cognito(self, 'Cognito')
        self.user_pool_id = cognito.user_pool.user_pool_id
        self.user_pool_client_id = cognito.client.user_pool_client_id

        api_fn = ApiFn(self, 'ApiFn',
                       dynamo_db_table=self.dynamodb_table,
                       kb_id=kb_id,
                       kb_data_src_id=kb_data_src_id,
                       kb_input_bucket=kb_input_bucket,
                       user_pool_id=cognito.user_pool.user_pool_id,
                      )

        self.endpoint = api_fn.endpoint
        self.domain_name = api_fn.domain_name

        # --- Event-Driven Status Update ---

        # 1. Lambda function to handle status updates
        status_updater_fn = _lambda.Function(
            self,
            "StatusUpdaterFunction",
            runtime=_lambda.Runtime.PYTHON_3_13,
            architecture=_lambda.Architecture.X86_64,
            handler="status_updater.handler",
            code=_lambda.Code.from_asset("twin/admin/src/app"),
            timeout=Duration.seconds(60),
            environment={
                "DDB_TABLE": self.dynamodb_table.table_name,
            },
        )

        # 2. Grant the new Lambda permission to write to the DynamoDB table
        self.dynamodb_table.grant_write_data(status_updater_fn)

        # 3. EventBridge rule to listen for Bedrock KB events
        rule = events.Rule(
            self,
            "BedrockKBIngestionJobRule",
            event_pattern=events.EventPattern(
                source=["aws.bedrock"],
                detail_type=["Bedrock Knowledge Base Ingestion Job State Change"]
            )
        )

        # 4. Set the Lambda function as the target for the rule
        # rule.add_target(targets.LambdaFunction(status_updater_fn))

        # --- DEBUGGING: Send events directly to a CloudWatch Log Group ---
        log_group = logs.LogGroup(self, "BedrockEventLogGroup")
        rule.add_target(targets.CloudWatchLogGroup(log_group))
