# Import AWS CDK core utilities and constructs
from aws_cdk import Duration, RemovalPolicy
from constructs import Construct

# Import AWS CDK modules for CloudFront, S3, and deployments
import aws_cdk.aws_cloudfront as cloudfront
import aws_cdk.aws_cloudfront_origins as origins
import aws_cdk.aws_s3 as s3
import aws_cdk.aws_s3_deployment as s3deploy


# Define a CDK Construct that represents the entire frontend infrastructure
class Frontend(Construct):
    # Will hold the CloudFront distribution domain name (public URL)
    domain_name: str

    def __init__(
        self, scope: Construct, id: str, backend_endpoint: str, **kwargs
    ) -> None:
        # Initialize the Construct superclass
        super().__init__(scope, id, **kwargs)

        # 🪣 Create an S3 bucket to host the static frontend files (HTML, JS, CSS)
        # RemovalPolicy.DESTROY means the bucket will be deleted when the stack is destroyed
        frontend_bucket = s3.Bucket(
            self,
            "FrontendBucket",
            removal_policy=RemovalPolicy.DESTROY,
        )

        # 🚀 Deploy local frontend build artifacts into the S3 bucket
        # The files come from ./weather/frontend/src (your local frontend build output)
        _ = s3deploy.BucketDeployment(
            self,
            "DeployFrontend",
            sources=[s3deploy.Source.asset("./weather/frontend/src")],
            destination_bucket=frontend_bucket,
        )
        # 🌐 Define an S3 origin for CloudFront, allowing read and list access
        s3_origin = origins.S3BucketOrigin.with_origin_access_control(
            frontend_bucket,
            origin_access_levels=[
                cloudfront.AccessLevel.READ,
                cloudfront.AccessLevel.LIST,
            ],
        )
        # ⚙️ Define an Origin Request Policy that forwards all cookies to the backend
        # (useful if your app or backend uses cookies for sessions/auth)
        origin_request_policy = cloudfront.OriginRequestPolicy(
            self,
            "OriginRequestPolicy",
            cookie_behavior=cloudfront.OriginRequestCookieBehavior.all(),
        )
        # 🔗 Define an HTTP origin for your backend Lambda Function URL
        # This allows CloudFront to route /chat requests to your backend API
        backend_origin = origins.HttpOrigin(
            domain_name=backend_endpoint,  # passed in from stack.py
            read_timeout=Duration.seconds(60),
            keepalive_timeout=Duration.seconds(60),
            connection_timeout=Duration.seconds(10),
        )
        # 🌍 Create a CloudFront distribution
        # - Serves static assets (default root = index.html)
        # - Routes specific paths (/chat) to backend
        distribution = cloudfront.Distribution(
            self,
            "Distribution",
            default_root_object="index.html",  # When someone visits "/", serve index.html
            default_behavior=cloudfront.BehaviorOptions(
                origin=s3_origin
            ),  # S3 static files
            additional_behaviors={
                "/chat": cloudfront.BehaviorOptions(
                    origin=backend_origin,
                    origin_request_policy=origin_request_policy,
                    allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
                    cache_policy=cloudfront.CachePolicy.CACHING_DISABLED,  # don't cache API responses
                )
            },
        )  # Any request to /chat is forwarded to the backend API
        # 🏁 Expose the CloudFront distribution's public URL (used in stack.py)
        self.domain_name = distribution.distribution_domain_name


"""
🧠 What’s Happening

Here’s the big picture:

1.  S3 Bucket

    Hosts your static frontend app (e.g., React, HTML, JS).
    Files are uploaded from ./weather/frontend/src.

2.  CloudFront Distribution

    Serves the frontend globally with low latency.
    Uses two origins:
        S3 origin: For static frontend files.
        HTTP origin (backend): For API calls like /chat.

3.  Dynamic Routing

    The /chat path is intercepted by CloudFront and forwarded to your backend Lambda’s URL (backend_endpoint).
4.  Frontend-Backend Integration

    The backend_endpoint is passed from stack.py:
        frontend = Frontend(self, 'Frontend', backend_endpoint=backend.domain_name)
    That domain_name was set in the backend construct as the Lambda Function URL.

So:

    Frontend (/chat) → CloudFront → Backend Lambda (Function URL)


5.  Output

    The Weather stack outputs:

FrontendURL = https://{frontend.domain_name}

You can open that in your browser to reach the deployed app.


🧩 Summary of Data Flow

| Request Type                      | CloudFront Route    | Origin                        | Description               |
| --------------------------------- | ------------------- | ----------------------------- | ------------------------- |
| `/`, `/index.html`, `/static/...` | default behavior    | S3                            | Serves frontend assets    |
| `/chat`                           | additional behavior | Lambda Function URL (backend) | Handles API/chat requests |





"""
