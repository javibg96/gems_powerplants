#!/usr/bin/env python3
import os

import aws_cdk as cdk

from src.gems_powerplant_stack import GemsPowerplantStack



company = 'ENGIE'

account_name = 'GEMS'

env = 'dev'


func = 'powerplants'

project = 'TranslationWordcountTracker'

component = "Stack"

# MAX 31 CHARACTERS
NAME = f"{env}-{account_name}-{hero}-{func}-{project}"

app = cdk.App()
GemsPowerplantStack(app, "GemsPowerplantStack", stack_name=NAME+ f"-{component}", id=project, name=NAME, env=cdk.Environment(account='XXXXXXXXX', region='eu-west-1'))



cdk.Tags.of(app).add("Project", project)

app.synth()
