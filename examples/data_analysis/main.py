#!/usr/bin/env python

import argparse
import yaml
import datetime
import sys

sys.path.insert(0, '.')
sys.path.insert(1, '../..')

import yaml
from bedrock_helpers import Agent, SupervisorAgent, Task
import uuid

def main(args):
    
    if args.recreate_agents == "false":
        Agent.set_force_recreate_default(False)
    else:
        Agent.set_force_recreate_default(True)

    with open('agents.yaml', 'r') as file:
        yaml_content = yaml.safe_load(file)

    code_interp_file_agent = Agent('code_interp_file_agent', yaml_content)    

    return 

    customer_data_agent = Agent('customer_data_agent', yaml_content)
    supervisor_description = "You are a supervisor agent for analyzing customer data." 

    supervisor_instructions = """
    You are a Supervisor Agent that plans and executes multi step tasks by 
    delegating work to sub-agents. You pretend that you handle requests directly. 
    When sending a request to a sub-agent, you are as explicit as possible, and
    you give enough context to help it do its expert job. 
    """ 
    # now create a supervisor agent capable of gathering appropriate customer data and analyzing that data
    account_manager_assistant = SupervisorAgent("account_manager_assistant", 
                                [customer_data_agent, 
                                code_interp_file_agent],
                                supervisor_instructions, 
                                supervisor_description)
    
    # get the tasks required
    with open('tasks.yaml', 'r') as file:
        yaml_content = yaml.safe_load(file)

    highest_priority_customer_task = Task('highest_priority_customer_task', yaml_content, 
                                          inputs={"s3_bucket": args.bucket})    

    # now use the supervisor to figure out which customer to focus on
    result = account_manager_assistant.invoke_with_tasks([
        highest_priority_customer_task],
        enable_trace=True, trace_level="core")
    print(f"Result:\n{result}")

    session_id=str(uuid.uuid4())
    result = account_manager_assistant.invoke(f"""
        which customer from North Dakota has the least YTD sales?
        use {args.bucket} bucket for interim results. be explicit about 
        this bucket when interacting with sub-agents.""",
        session_id=session_id,
        enable_trace=True, trace_level="core")
    print(f"Result:\n{result}")

    result = account_manager_assistant.invoke("""
        Nice. And what is the average YTD sales per customer?""",
        session_id=session_id,
        enable_trace=True, trace_level="core")
    print(f"Result:\n{result}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument("--recreate_agents", 
                        required=True, 
                        help="False if reusing existing agents.")
    parser.add_argument("--bucket", required=True, help="s3 bucket to use for interim and final results.")

    args = parser.parse_args()
    main(args)
