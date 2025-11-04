#!/usr/bin/env python3
import aws_cdk as cdk
from weather.stack import Weather

app = cdk.App()
_ = Weather(app, "weather")
app.synth()


"""
#!/usr/bin/env python3  # Allows running the script directly from the shell

import aws_cdk as cdk   # Import the AWS CDK core library
from weather.stack import Weather  # Import your custom stack class from weather/stack.py

# Create the CDK application (root construct)
app = cdk.App()

# Instantiate a stack called "weather" from your Weather class
_ = Weather(app, 'weather')

# Synthesize the app to a CloudFormation template
app.synth()



| Step | Code                      | What It Does                                         |
| ---- | ------------------------- | ---------------------------------------------------- |
| 1    | `app = cdk.App()`         | Creates the root CDK app                             |
| 2    | `Weather(app, 'weather')` | Adds a stack that defines AWS resources              |
| 3    | `app.synth()`             | Converts to a CloudFormation template for deployment |

"""
