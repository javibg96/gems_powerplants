from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as lambda_,
    aws_iam as iam,
    aws_logs as logs,
    RemovalPolicy,
    CfnResource,
    CfnOutput
)
from constructs import Construct

class GemsPowerplantStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, name: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        role = iam.Role(self, "lambdaIAMExecutionRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            role_name=name+'_role')

        # Define the Lambda function resource
        Powerplant_function = lambda_.Function(
            self, 
            name,
            function_name=name,
            role=role,
            description='',
            timeout=Duration.seconds(900),
            memory_size=10240,
            runtime=lambda_.Runtime.PYTHON_3_11,
            code=lambda_.DockerImageCode.from_image_asset(
                # Directory relative to where you execute cdk deploy
                # contains a Dockerfile with build instructions
                directory="src/lambda_code"
            ),
            layers= [
                    lambda_.LayerVersion.from_layer_version_arn(
                        self,
                        'AWSDataWrangler-Python311',
                        'arn:aws:lambda:eu-west-1:336392948345:layer:AWSSDKPandas-Python311:10')
                    ],
            retry_attempts=0
        )
        
        # Set up the Lambda Function URL
        cfnFuncUrl = CfnResource(
            scope=self,
            id="lambdaFuncUrl",
            type="AWS::Lambda::Url",
            properties={
                "TargetFunctionArn": self.Powerplant_function.function_arn,
                "AuthType": "NONE",
                "Cors": {"AllowOrigins": ["*"]},
            },
        )

        # Give everyone permission to invoke the Function URL
        CfnResource(
            scope=self,
            id="funcURLPermission",
            type="AWS::Lambda::Permission",
            properties={
                "FunctionName": self.Powerplant_function.function_name,
                "Principal": "*",
                "Action": "lambda:InvokeFunctionUrl",
                "FunctionUrlAuthType": "NONE",
            },
        )

        # Get the Function URL as output
        CfnOutput(
            scope=self,
            id="funcURLOutput",
            value=cfnFuncUrl.get_att(attribute_name="FunctionUrl").to_string(),
        )

        #log group
        #------------------------
        log_group = logs.LogGroup(self, f"{name}-LogGroup",
            log_group_name=f'/aws/lambda/{name}',
            removal_policy=RemovalPolicy.DESTROY,
            retention=logs.RetentionDays.ONE_WEEK
            )
        
        log_group.grant_write(role)