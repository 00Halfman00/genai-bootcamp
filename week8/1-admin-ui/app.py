#!/usr/bin/env python3
import os

import aws_cdk as cdk

from kb.stack import KnowledgeBase
from twin.stack import Twin

env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region='us-west-2')
app = cdk.App()
kb = KnowledgeBase(app, "KnowledgeBaseStack", env=env)
_ = Twin(app, "Twin",
         kb_arn=kb.kb.knowledge_base_arn,
         kb_id=kb.kb.knowledge_base_id,
         kb_data_src_id=kb.kb.data_source_id,
         kb_input_bucket=kb.input_bucket,
         custom_domain_name="00oscar00.com",
         custom_certificate_arn="arn:aws:acm:us-east-1:078109852507:certificate/25de5f2e-5c03-4cfa-95f6-1b29c99cf671",
         env=env,
        )

app.synth()
