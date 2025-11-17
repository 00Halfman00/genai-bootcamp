#!/usr/bin/env python3
import os

import aws_cdk as cdk

from kb.stack import KnowledgeBase

env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region='us-west-2')
app = cdk.App()
_ = KnowledgeBase(app, "KnowledgeBaseStack", env=env)
app.synth()
