"""
A small visual of how CDK’s construct hierarchy looks (with App → Stack → Construct → Resources).
It helps make this idea click very clearly.
"""

# A visual walkthrough of how CDK constructs nest and how __init__ fits into the hierarchy.


"""
🌳 The AWS CDK Construct Tree
  Everything in CDK is part of a tree of constructs.
  It looks like this for app:

  App
  └── Weather (Stack)
      ├── Backend (Construct)
      │   ├── StateBucket (s3.Bucket)
      │   └── WeatherBackend (lambda.DockerImageFunction)
      └── Frontend (Construct)
          └── (Resources for hosting frontend)

"""

"""
🧱 1. App level (app.py)

    app = cdk.App()
    weather_stack = Weather(app, "weather")
    app.synth()
"""

# cdk.App() is the root of everything.
# When you add a stack (Weather), it becomes a child of the app.
# app.synth() turns the tree into a CloudFormation template.


"""
🗂️ 2. Stack level (stack.py)

  backend = Backend(self, 'Backend')
  frontend = Frontend(self, 'Frontend', backend_endpoint=backend.domain_name)

"""

# The Weather stack acts as a container for the Backend and Frontend constructs.
# Each of these constructs is responsible for building a specific part of your app.
# The stack’s __init__ runs when the CDK builds the app.

"""
⚙️ 3. Construct level (infra.py)
  Inside Backend.__init__:

  state_bucket = s3.Bucket(self, 'StateBucket')
  fn = _lambda.DockerImageFunction(self, 'WeatherBackend', ...)

"""

# Each of these is a child resource of the Backend construct.
# They’re tracked automatically because you pass self as the scope (the construct that owns them).


"""
📦 4. CDK Tree Visualization (Conceptual)
  When the CDK synthesizes your app, it internally builds a tree like this:

    App
  └── weather (Stack)
      ├── Backend (Construct)
      │   ├── StateBucket (AWS::S3::Bucket)
      │   ├── WeatherBackend (AWS::Lambda::Function)
      │   └── WeatherBackendUrl (AWS::Lambda::Url)
      ├── Frontend (Construct)
      │   └── (e.g. CloudFront Distribution, S3 Bucket)
      └── FrontendURL (AWS::CloudFormation::Output)


  This is what eventually becomes the CloudFormation template that AWS uses to actually deploy the resources.
"""


"""
🧠 Key idea
Each level “owns” the next:

| Level     | Class                | Role                                                     |
| --------- | -------------------- | -------------------------------------------------------- |
| Root      | `cdk.App`            | The top-level CDK application                            |
| Stack     | `cdk.Stack`          | A deployable unit (translates to a CloudFormation stack) |
| Construct | `Construct` subclass | Logical grouping of resources                            |
| Resource  | e.g. `s3.Bucket`     | Actual AWS service resources                             |

"""

"""
🧩 Why the constructor (__init__) is key

  When you call:
  backend = Backend(self, "Backend")

  You’re literally inserting a subtree under the stack node.
  Your __init__ method defines what’s inside that subtree:

    the Lambda,
    the S3 bucket,
    and the permissions.
"""

#####################################################################


"""
let’s go step by step through how scope, id, and self connect between the layers in your CDK app, using Weather → Backend → S3/Lambda example.

🧭 Big Picture: Parent–Child Relationship in CDK

Every CDK construct (App, Stack, or your own class like Backend) forms part of a tree.
Each construct’s constructor (__init__) follows this pattern:

  def __init__(self, scope: Construct, id: str, **kwargs)

    Parameter	Meaning
    scope	The parent construct that this one lives inside.
    id	A unique name within the parent scope.
    self	The current construct being created (the child).
    🧱 How It Works in Your Code

Let’s start from the top:

1️⃣ In app.py
  app = cdk.App()
  _ = Weather(app, "weather")


🧩 Here:

  app → scope
  "weather" → id

The new Weather stack becomes a child of app.

📊 Relationship:

App (root)
└── Weather (Stack)

2️⃣ Inside stack.py (Weather Stack)
backend = Backend(self, "Backend")
frontend = Frontend(self, "Frontend", backend_endpoint=backend.domain_name)


🧩 Here:

self (the current stack) is passed as the scope to both Backend and Frontend.

"Backend" and "Frontend" are unique IDs.

📊 Relationship:

App
└── Weather (Stack)
    ├── Backend (Construct)
    └── Frontend (Construct)

3️⃣ Inside infra.py (Backend Construct)
state_bucket = s3.Bucket(self, "StateBucket")
fn = _lambda.DockerImageFunction(self, "WeatherBackend", ...)


🧩 Here:

self (the Backend construct) becomes the scope for the bucket and function.

"StateBucket" and "WeatherBackend" are IDs for those resources.

📊 Relationship:

App
└── Weather (Stack)
    ├── Backend (Construct)
    │   ├── StateBucket (s3.Bucket)
    │   └── WeatherBackend (lambda.Function)

🪄 Visualization: How the Parameters Flow
app = cdk.App()
│
└── Weather(app, "weather")
    │
    ├── Backend(self, "Backend")   ← scope = Weather
    │    │
    │    ├── s3.Bucket(self, "StateBucket")   ← scope = Backend
    │    └── _lambda.Function(self, "WeatherBackend")
    │
    └── Frontend(self, "Frontend") ← scope = Weather


Each level passes itself down as scope to the constructs it creates.

💡 Why This Matters

CDK uses these scope → child relationships to:

Build the construct tree (so CloudFormation knows dependencies).

Auto-generate resource names and paths.

Ensure resource uniqueness within each level (the id must be unique only within its scope).

So yes — the constructor in your Backend class isn’t just creating attributes.
It’s defining the entire sub-tree of AWS resources that belong to that construct.
"""


################################################################################

"""
Awesome 👍 let’s visualize how this structure shows up inside AWS CloudFormation when your CDK app is synthesized and deployed.

🧱 Recap of Your Code Hierarchy

You have:

app.py
└── Weather (Stack)
    ├── Backend (Construct)
    │   ├── StateBucket (S3)
    │   └── WeatherBackend (Lambda)
    └── Frontend (Construct)
        ├── (Probably some S3/CloudFront resources)

🗂️ How CDK Turns This Into CloudFormation

When you run:
uv run cdk synth

    CDK traverses this construct tree and generates a single CloudFormation template for your Weather stack.
    Each construct becomes a section of the template, and each resource (like the S3 bucket or Lambda)
    becomes a CloudFormation resource with a logical ID.

🧩 Example CloudFormation Logical IDs

Based on the hierarchy, CDK will generate something roughly like this:

    Construct Path	Logical ID in CloudFormation
    Weather/Backend/StateBucket	BackendStateBucket9C1B9E05
    Weather/Backend/WeatherBackend	BackendWeatherBackendLambdaE7BEE3A5
    Weather/Frontend/...	FrontendDistributionC34FDF45
    Weather/Frontend/...	FrontendBucket9C42FA8F
    Weather/FrontendURL (output)	FrontendURL

CDK appends a unique hash to ensure logical IDs are consistent and unique, even if you rename constructs.

🧭 How AWS Knows What to Deploy

When you run:
    uv run cdk deploy

CDK:

Synthesizes your Python constructs → JSON CloudFormation template.
Uploads it to AWS CloudFormation.
CloudFormation then:

    Creates an S3 bucket for state storage.
    Builds and uploads your Lambda Docker image.
    Sets up any IAM roles or permissions.
    Outputs the frontend URL you defined.

🪞 Why the Construct Tree Matters

This tree structure gives you:

    Predictable naming (no resource collisions).
    Scoped permissions and cleanup (destroy a stack = remove all children).
    Composable infrastructure — you can reuse Backend or Frontend elsewhere easily.

✅ In short:

    Every CDK construct is a node in a tree.
    scope defines where that node lives.
    id names it within that level.
    CDK uses that tree to generate CloudFormation logical IDs and manage dependencies.
"""


"""
👍 — Here’s what your cdk synth output would roughly look like
once your app.py, stack.py, and backend/infra.py are processed.

This is a simplified example of what CDK generates behind the scenes
— the real one is longer, but this will make it crystal clear
how your Python constructs translate into AWS resources.

🧾 CloudFormation Template (Simplified)

AWSTemplateFormatVersion: '2010-09-09'
Description: Weather Stack

Resources:
  # 🪣 S3 Bucket to hold backend state
  BackendStateBucket9C1B9E05:
    Type: AWS::S3::Bucket
    Properties:
      DeletionPolicy: Delete  # from RemovalPolicy.DESTROY
      UpdateReplacePolicy: Delete

  # ⚙️ IAM Role for Lambda execution
  BackendWeatherBackendServiceRoleE9B7E8F5:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: lambda.amazonaws.com
            Action: sts:AssumeRole
      Policies:
        - PolicyName: InvokeBedrockAndS3
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action:
                  - bedrock:InvokeModel
                  - bedrock:InvokeModelWithResponseStream
                Resource: "*"
              - Effect: Allow
                Action:
                  - s3:GetObject
                  - s3:PutObject
                Resource:
                  - !Sub "${BackendStateBucket9C1B9E05.Arn}/*"

  # 🐳 Lambda function (built from Dockerfile)
  BackendWeatherBackendF50D03EE:
    Type: AWS::Lambda::Function
    Properties:
      PackageType: Image
      Timeout: 60
      Role: !GetAtt BackendWeatherBackendServiceRoleE9B7E8F5.Arn
      Code:
        ImageUri: "<ECR image URI built from weather/backend/src/Dockerfile>"
      Environment:
        Variables:
          MODEL_ID: global.anthropic.claude-haiku-4-5-20251001-v1:0
          AWS_LWA_INVOKE_MODE: response_stream
          STATE_BUCKET: !Ref BackendStateBucket9C1B9E05

  # 🌐 Lambda Function URL
  BackendWeatherBackendUrl7E1A2A54:
    Type: AWS::Lambda::Url
    Properties:
      TargetFunctionArn: !Ref BackendWeatherBackendF50D03EE
      AuthType: NONE
      Cors:
        AllowOrigins: ['*']
        AllowMethods: ['*']
      InvokeMode: RESPONSE_STREAM

  # 🔗 (Optional) Lambda Permission to allow public access
  BackendWeatherBackendPermissionF6A74CE2:
    Type: AWS::Lambda::Permission
    Properties:
      Action: lambda:InvokeFunctionUrl
      FunctionName: !Ref BackendWeatherBackendF50D03EE
      Principal: "*"

  # 🌍 CloudFormation Output: Frontend URL
  FrontendURL:
    Type: AWS::CloudFormation::Output
    Value: !Sub "https://${FrontendDistribution.DomainName}"
    Description: Frontend UI URL


"""


"""
🧠 What’s Happening
Each Construct (like Backend) gets expanded into multiple CloudFormation resources.
CDK automatically:

    Names them uniquely.
    Connects them together with Ref and GetAtt.
    Applies IAM and permissions.

Your Weather stack is just a Python wrapper around this infrastructure definition.

So when you ran:
    uv run cdk deploy

    AWS CloudFormation deployed this YAML (generated by CDK) to your account and created:
    The Lambda container (built via Docker)
    The S3 bucket for state
    The public function URL
    The IAM role + policies
"""


########################################################

"""
Now that you’ve added the frontend/infra.py,
here’s how the updated CloudFormation template would look conceptually
(i.e., what cdk synth will now generate).
This version includes all your backend and frontend resources:

🧾 Full Weather App CloudFormation Template (Simplified)

AWSTemplateFormatVersion: '2010-09-09'
Description: Weather Stack

Resources:
  # ======================
  # 🪣 Backend Resources
  # ======================
  BackendStateBucket9C1B9E05:
    Type: AWS::S3::Bucket
    DeletionPolicy: Delete
    UpdateReplacePolicy: Delete

  BackendWeatherBackendServiceRoleE9B7E8F5:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: lambda.amazonaws.com
            Action: sts:AssumeRole
      Policies:
        - PolicyName: InvokeBedrockAndS3
          PolicyDocument:
            Statement:
              - Effect: Allow
                Action:
                  - bedrock:InvokeModel
                  - bedrock:InvokeModelWithResponseStream
                Resource: "*"
              - Effect: Allow
                Action:
                  - s3:GetObject
                  - s3:PutObject
                Resource:
                  - !Sub "${BackendStateBucket9C1B9E05.Arn}/*"

  BackendWeatherBackendF50D03EE:
    Type: AWS::Lambda::Function
    Properties:
      PackageType: Image
      Timeout: 60
      Role: !GetAtt BackendWeatherBackendServiceRoleE9B7E8F5.Arn
      Code:
        ImageUri: "<ECR image URI built from weather/backend/src/Dockerfile>"
      Environment:
        Variables:
          MODEL_ID: global.anthropic.claude-haiku-4-5-20251001-v1:0
          AWS_LWA_INVOKE_MODE: response_stream
          STATE_BUCKET: !Ref BackendStateBucket9C1B9E05

  BackendWeatherBackendUrl7E1A2A54:
    Type: AWS::Lambda::Url
    Properties:
      TargetFunctionArn: !Ref BackendWeatherBackendF50D03EE
      AuthType: NONE
      Cors:
        AllowOrigins: ['*']
        AllowMethods: ['*']
      InvokeMode: RESPONSE_STREAM

  BackendWeatherBackendPermissionF6A74CE2:
    Type: AWS::Lambda::Permission
    Properties:
      Action: lambda:InvokeFunctionUrl
      FunctionName: !Ref BackendWeatherBackendF50D03EE
      Principal: "*"

  # ======================
  # 🎨 Frontend Resources
  # ======================
  FrontendBucketB5D21977:
    Type: AWS::S3::Bucket
    DeletionPolicy: Delete
    UpdateReplacePolicy: Delete

  FrontendBucketDeploymentA839D12F:
    Type: Custom::CDKBucketDeployment
    Properties:
      ServiceToken: <Lambda ARN for CDK’s internal deploy handler>
      SourceBucketNames: [ "<CDKAssetBucket>" ]
      SourceObjectKeys: [ "<zipped frontend assets from ./weather/frontend/src>" ]
      DestinationBucketName: !Ref FrontendBucketB5D21977

  # 🌐 CloudFront Distribution
  FrontendDistributionC57E0A77:
    Type: AWS::CloudFront::Distribution
    Properties:
      DistributionConfig:
        Enabled: true
        DefaultRootObject: "index.html"
        Origins:
          - DomainName: !GetAtt FrontendBucketB5D21977.RegionalDomainName
            Id: S3Origin
            S3OriginConfig: {}
          - DomainName: !GetAtt BackendWeatherBackendUrl7E1A2A54.FunctionUrlDomainName
            Id: BackendOrigin
            CustomOriginConfig:
              OriginProtocolPolicy: https-only
              OriginReadTimeout: 60
        DefaultCacheBehavior:
          TargetOriginId: S3Origin
          ViewerProtocolPolicy: redirect-to-https
          AllowedMethods: [GET, HEAD]
        CacheBehaviors:
          - PathPattern: "/chat"
            TargetOriginId: BackendOrigin
            ViewerProtocolPolicy: https-only
            AllowedMethods: [GET, POST, PUT, DELETE, OPTIONS]
            CachePolicyId: !Ref "AWS::CloudFront::CachePolicy-CACHING_DISABLED"

  # ======================
  # 🔗 Outputs
  # ======================
  FrontendURL:
    Type: AWS::CloudFormation::Output
    Value: !Sub "https://${FrontendDistributionC57E0A77.DomainName}"
    Description: "Frontend UI URL"

"""


"""
🧠 What’s new here

1.  FrontendBucket — Stores your static web assets (HTML, JS, CSS).
2.  BucketDeployment — Automatically uploads your frontend files during deployment (cdk deploy).
3.  CloudFront Distribution —
      Serves your static site from the S3 bucket.
      Proxies /chat API requests to the backend Lambda URL.
4.  Output — Publishes the CloudFront distribution’s domain name as your frontend app’s public URL.
"""


#######################  ADDING TOOLS  ###########################################

"""
⚙️ 1. How to make it a “tool” for an LLM

In modern LLM setups, a “tool” (sometimes called a function call or action) is just a
piece of code the model can call to perform a real-world task (like fetching weather).
So, you could expose this function to your model:


weather/
├── backend/
│   ├── infra.py
│   └── src/
│       └── app.py   👈 your Lambda logic lives here
├── frontend/
│   ├── infra.py
│   └── src/
│       └── index.html

| Part                 | Purpose                                            | Where weather logic belongs                                 |
| -------------------- | -------------------------------------------------- | ----------------------------------------------------------- |
| **Frontend**         | Static UI (React, HTML, etc.)                      | ❌ *Doesn’t call APIs directly except your backend endpoint* |
| **Backend (Lambda)** | Executes Python code, interacts with external APIs | ✅ *Place your `get_weather()` here*                         |


"""
