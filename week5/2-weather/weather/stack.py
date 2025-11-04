import aws_cdk as cdk
from weather.backend.infra import Backend
from weather.frontend.infra import Frontend


class Weather(cdk.Stack):
    def __init__(self, scope: cdk.App, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        backend = Backend(self, "Backend")
        frontend = Frontend(self, "Frontend", backend_endpoint=backend.domain_name)

        _ = cdk.CfnOutput(
            self,
            "FrontendURL",
            value=f"https://{frontend.domain_name}",
            description="Frontend UI URL",
        )


"""

class Weather(cdk.Stack):
    def __init__(self, scope: cdk.App, id: str, **kwargs) -> None:
        # Initialize the base Stack class
        super().__init__(scope, id, **kwargs)

        # Create the backend infrastructure (e.g., API Gateway + Lambda + DynamoDB, etc.)
        backend = Backend(self, 'Backend')

        # Create the frontend infrastructure (e.g., S3 static site + CloudFront)
        # Pass the backend's endpoint so the frontend knows where to send API calls
        frontend = Frontend(self, 'Frontend', backend_endpoint=backend.domain_name)

        # Output the frontend's domain name after deployment
        _ = cdk.CfnOutput(
            self,
            'FrontendURL',
            value=f"https://{frontend.domain_name}",    # CloudFront or custom domain for UI
            description='Frontend UI URL'               # Appears in the CDK output in terminal
        )


##################################################################


🧠 Conceptual Breakdown
1. Weather Stack

    This is your main CDK stack, named Weather.
    Each stack represents a logical unit of infrastructure, and when deployed,
    it becomes a CloudFormation stack in AWS.

2. Backend construct

    Backend(self, 'Backend') likely sets up:

        A Lambda function that handles API requests
        An API Gateway endpoint that routes HTTP traffic
        Possibly a DynamoDB table or S3 bucket for storing data

    When it finishes, it probably exposes an attribute like domain_name (e.g., API Gateway URL).


3. Frontend construct

    Frontend(self, 'Frontend', backend_endpoint=backend.domain_name) likely creates:

        An S3 bucket to host static files (HTML/JS)
        A CloudFront distribution for HTTPS and global caching
        Possibly Route53 DNS configuration

    It receives the backend endpoint so it can make API calls to it.

4. CloudFormation Output

    This line:

        cdk.CfnOutput(
            self,
            'FrontendURL',
            value=f"https://{frontend.domain_name}",
            description='Frontend UI URL'
        )


    adds an output to your CloudFormation stack — when you run cdk deploy,
    you’ll see something like:

    Outputs:
    Weather.FrontendURL = https://d123abc4.cloudfront.net


That’s your live frontend URL.

🏗️ Deployment flow

    1.  You synthesize the CDK app:

        cdk synth


→ Generates a CloudFormation template (cdk.out/weather.template.json).

    2.  You deploy the stack:

        cdk deploy


→ Creates all resources (backend, frontend, permissions, etc.) on AWS.

    3.  After deployment, you’ll get an output like:

        Weather.FrontendURL = https://abcdef123.cloudfront.net


        which you can visit to see the app.
"""
