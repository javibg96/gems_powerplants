from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as lambda_,
    aws_iam as iam,
    aws_logs as logs,
    RemovalPolicy,
    aws_apigateway as apigateway,
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
            code=lambda_.Code.from_asset("cdk_lambda/lambda_code"),
            handler="powerplants_main.handler",
            # layers= [
            #         lambda_.LayerVersion.from_layer_version_arn(
            #             self,
            #             'AWSDataWrangler-Python311',
            #             'arn:aws:lambda:eu-west-1:336392948345:layer:AWSSDKPandas-Python311:10')
            #         ],
            retry_attempts=0
        )
        # Define the API Gateway resource
        api = apigateway.LambdaRestApi(
            self,
            "PowerplantApi",
            handler = Powerplant_function,
            proxy = False,
        )
        
        post_resource = api.root.add_resource("productionplan")
        post_resource.add_method("POST")

        #log group
        #------------------------
        log_group = logs.LogGroup(self, f"{name}-LogGroup",
            log_group_name=f'/aws/lambda/{name}',
            removal_policy=RemovalPolicy.DESTROY,
            retention=logs.RetentionDays.ONE_WEEK
            )
        
        log_group.grant_write(role)