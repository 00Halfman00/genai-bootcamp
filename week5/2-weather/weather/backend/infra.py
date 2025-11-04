from aws_cdk import Duration, Fn, RemovalPolicy
from constructs import Construct
import aws_cdk.aws_iam as iam
import aws_cdk.aws_lambda as _lambda
import aws_cdk.aws_s3 as s3


class Backend(Construct):
    # Backend is defined as a CDK Construct — a reusable building block.
    # It will be used inside your Weather stack.
    # It defines two key attributes:
    # endpoint: the full Lambda function URL
    # domain_name: the hostname part of that URL (for use by the frontend)
    endpoint: str
    domain_name: str

    # __init__ is the constructor method — it runs once when you create an instance of the class.
    # scope and id are required by all AWS CDK constructs.
    # scope: The parent construct — in this case, the Weather stack that’s creating the backend.
    # id: The logical identifier for this construct (used in CloudFormation naming).
    def __init__(self, scope: "Construct", id: str) -> None:
        # This calls the parent class’s constructor (here, Construct.__init__()).
        # It’s necessary because Backend inherits from Construct, and the CDK needs that setup
        # to track all resources (buckets, lambdas, etc.) that you create.
        super().__init__(scope, id)

        # All the code inside the __init__ method (and indented under it) is part of the constructor.

        """  Create an S3 bucket  """
        # Creates an S3 bucket named StateBucket.
        # The removal_policy=RemovalPolicy.DESTROY means the bucket will be deleted
        # when the stack is destroyed (good for dev/lab setups, but not for production).
        # The bucket is likely used to store temporary state (like chat sessions, weather data, or model responses).
        state_bucket = s3.Bucket(
            self,
            "StateBucket",
            removal_policy=RemovalPolicy.DESTROY,
        )

        """  Define the Lambda function (Docker-based)  """
        # This Lambda is built from a Docker image in weather/backend/src/Dockerfile.
        # That means your app logic and dependencies are packaged as a container
        # — ideal for custom dependencies (like the AWS Bedrock SDK or AI inference logic).
        fn = _lambda.DockerImageFunction(
            self,
            "WeatherBackend",
            function_name="WeatherBackend",
            timeout=Duration.seconds(60),
            architecture=_lambda.Architecture.X86_64,
            code=_lambda.DockerImageCode.from_image_asset(
                directory="weather/backend/src", file="Dockerfile"
            ),
            # Environment variables:
            # MODEL_ID: the Bedrock model to use (here, Claude Haiku 4.5).
            # AWS_LWA_INVOKE_MODE: enables response streaming, so results stream back progressively.
            # STATE_BUCKET: passes the name of the S3 bucket for the function to use.
            environment={
                "MODEL_ID": "global.anthropic.claude-haiku-4-5-20251001-v1:0",
                "AWS_LWA_INVOKE_MODE": "response_stream",
                "STATE_BUCKET": state_bucket.bucket_name,
            },
        )

        """  Grant S3 access  """
        # Gives the Lambda read/write permissions to the S3 bucket — so it can store or retrieve data.
        _ = state_bucket.grant_read_write(fn)

        """  Add IAM policy for Bedrock  """
        # Add Bedrock permissions to the Lambda function
        # Grants the Lambda permission to call Bedrock models, including streaming ones.
        # "*" means all models; you could scope this down to your specific model ARN for tighter security.
        fn.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "bedrock:InvokeModelWithResponseStream",
                    "bedrock:InvokeModel",
                ],
                resources=["*"],
            )
        )
        """  Create a Function URL  """
        # This creates a public HTTPS endpoint (a “Lambda Function URL”).
        # auth_type.NONE means no authentication (anyone can call it — again fine for testing, not for production).
        # invoke_mode.RESPONSE_STREAM allows real-time streaming responses from Bedrock (e.g., text generating live).
        # CORS allows requests from any origin, so your frontend JavaScript can call it directly.
        fn_url = fn.add_function_url(
            auth_type=_lambda.FunctionUrlAuthType.NONE,
            invoke_mode=_lambda.InvokeMode.RESPONSE_STREAM,
            cors=_lambda.FunctionUrlCorsOptions(
                allowed_methods=[_lambda.HttpMethod.ALL],
                allowed_origins=["*"],
            ),
        )

        """  Extract and expose URLs  """
        # fn_url.url might look like:
        # https://abcdefg123.lambda-url.us-west-2.on.aws/
        # Fn.split('/', ...) splits by /,
        # and Fn.select(2, ...) picks the third element (index 2), which gives:
        # abcdefg123.lambda-url.us-west-2.on.aws
        # That domain is passed to the frontend (so it knows where to send API calls).
        self.endpoint = fn_url.url
        self.domain_name = Fn.select(
            2, Fn.split("/", self.endpoint)
        )  # Remove the protocol part from the URL


"""
🧠 Summary

| Component      | Purpose                              | AWS Service         |
| -------------- | ------------------------------------ | ------------------- |
| `state_bucket` | Stores persistent or temporary state | S3                  |
| `fn`           | Backend logic (runs AI calls)        | Lambda              |
| `fn_url`       | Public endpoint for frontend to call | Lambda Function URL |
| IAM policy     | Allows Lambda to use Bedrock         | IAM                 |
| `domain_name`  | Hostname part of the Lambda URL      | (Used by frontend)  |


🔁 Big Picture
Here’s how it connects with the rest of your app:

+----------------+
| Frontend (S3)  |  --->  https://abcdefg.lambda-url...on.aws  --->  Bedrock Claude model
|  (HTML/JS)     |                                      |
+----------------+                                      |
         ^                                              |
         |----------------------------------------------+
                          S3 Bucket (State)



🧠 What comes after

All the code inside the __init__ method (and indented under it) is part of the constructor.
That means everything that follows — such as:

    state_bucket = s3.Bucket(...)
    fn = _lambda.DockerImageFunction(...)
    _ = state_bucket.grant_read_write(fn)
    fn.add_to_role_policy(...)
    fn_url = fn.add_function_url(...)
    self.endpoint = fn_url.url
    self.domain_name = Fn.select(...)


— is all being executed when the Backend construct is created.

In other words:

When you run this line in stack.py:
backend = Backend(self, 'Backend')

    It immediately runs the constructor (__init__), which:
    Creates the S3 bucket
    Builds and configures the Lambda function
    Grants permissions
    Sets up the function URL
    Saves the endpoint and domain name as attributes on self

After the constructor finishes, your new backend object exists, fully built, and ready to be used by other parts of your CDK app (like the frontend).

⚙️ Analogy

Think of it like initializing a robot:

backend = Backend(self, "Backend")
This triggers the robot’s startup routine:

install bucket
upload Lambda image
attach IAM permissions
expose endpoint

When it’s done booting, backend.endpoint and backend.domain_name are ready to be passed to your frontend.

✅ In summary
Concept	Explanation

__init__	                    Constructor — runs when you create a Backend
super().__init__()	            Initializes the CDK base class
All indented code under it	    Defines and configures the AWS resources for this construct
End of method	                When it finishes, Backend is fully provisioned as part of the CDK app

"""
