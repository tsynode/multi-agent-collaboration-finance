#!/usr/bin/env python

import sys
sys.path.insert(0, '..')
sys.path.insert(1, '../..')

import datetime
import traceback
import argparse
import yaml
import uuid
from textwrap import dedent

from bedrock_helpers import Agent, SupervisorAgent, Task, region, account_id

def main(args):

    if args.recreate_agents == "false":
        Agent.set_force_recreate_default(False)
    else:
        Agent.set_force_recreate_default(True)

    inputs = {
        'customer_domain': args.web_domain,
        'project_description': args.project,
        'bucket': args.bucket
    }    

    with open('tasks.yaml', 'r') as file:
        yaml_content = yaml.safe_load(file)

    research_task = Task('research_task', yaml_content, inputs)
    marketing_strategy_task = Task('marketing_strategy_task', yaml_content, inputs)
    campaign_idea_task =  Task('campaign_idea_task', yaml_content, inputs)
    copy_creation_task = Task('copy_creation_task', yaml_content, inputs)
    final_edit_task = Task('final_edit_task', yaml_content, inputs)

    with open('agents.yaml', 'r') as file:
        yaml_content = yaml.safe_load(file)

    lead_market_analyst = Agent('lead_market_analyst', yaml_content,
                    tool_code=f"arn:aws:lambda:{region}:{account_id}:function:websearch_lambda",
                    tool_defs=[{ 
                        "name": "web_search", 
                        "description": "Searches the web for information", 
                        "parameters": {
                            "search_query": {
                                "description": "The query to search the web with",
                                "type": "string",
                                "required": True},
                            "target_website": {
                                "description": "The specific website to search including its domain name. If not provided, the most relevant website will be used",
                                "type": "string", "required": False},
                            "topic": {
                                "description": "The topic being searched. 'news' or 'general'. Helps narrow the search when news is the focus.",
                                "type": "string", "required": False},
                            "days": {
                                "description": "The number of days of history to search. Helps when looking for recent events or news.",
                                "type": "string", "required": False}
                        }
                    }])
    chief_strategist = Agent('chief_strategist', yaml_content,
                    tool_code=f"arn:aws:lambda:{region}:{account_id}:function:websearch_lambda",
                    tool_defs=[{ 
                        "name": "web_search", 
                        "description": "Searches the web for information", 
                        "parameters": {
                            "search_query": {
                                "description": "The query to search the web with",
                                "type": "string",
                                "required": True},
                            "target_website": {
                                "description": "The specific website to search including its domain name. If not provided, the most relevant website will be used",
                                "type": "string", "required": False},
                            "topic": {
                                "description": "The topic being searched. 'news' or 'general'. Helps narrow the search when news is the focus.",
                                "type": "string", "required": False},
                            "days": {
                                "description": "The number of days of history to search. Helps when looking for recent events or news.",
                                "type": "string", "required": False}
                        }
                    }])
    chief_content_officer = Agent('chief_content_officer', yaml_content)
    content_creator = Agent('content_creator', yaml_content)
    agent_storage_manager = Agent('agent_storage_manager', yaml_content,
                                tool_code=f"arn:aws:lambda:{region}:{account_id}:function:agent_file_store",
                                tool_defs=[{ 
                                    "name": "save_file", 
                                    "description": "Saves content to a named file in the file store.", 
                                    "parameters": {
                                        "bucket": {
                                            "description": "The s3 bucket to use for file storage.",
                                            "type": "string",
                                            "required": True},
                                        "file_name": {
                                            "description": "The name of the file to save including a file extension. It can have a folder prefix.",
                                            "type": "string", "required": True},
                                        "folder_name": {
                                            "description": "The name of the folder to use, helping organize the file storage.",
                                            "type": "string", "required": True},
                                        "contents": {
                                            "description": "The contents to be saved to the file.",
                                            "type": "string", "required": True}
                                    }
                                },
                                {
                                    "name": "get_file", 
                                    "description": "Returns the content found in a named file in the file store.", 
                                    "parameters": {
                                        "bucket": {
                                            "description": "The s3 bucket to use for file storage.",
                                            "type": "string",
                                            "required": True},
                                        "file_name": {
                                            "description": "The name of the file to retrieve including a file extension. It can have a folder prefix.",
                                            "type": "string", "required": True},
                                        "folder_name": {
                                            "description": "The name of the folder use when finding the file whose contents to retrieve.",
                                            "type": "string", "required": True}
                                    }
                                }]
                            )
    
    print("\n\nCreating marketing_strategy_agent as a supervisor agent...\n\n")
    startup_advisor = SupervisorAgent("startup_advisor", yaml_content,
                                [lead_market_analyst, chief_strategist, content_creator,
                                chief_content_officer, agent_storage_manager])
    
    if args.recreate_agents == "false":
        print("\n\nInvoking supervisor agent...\n\n")

        time_before_call = datetime.datetime.now()
        print(f"time before call: {time_before_call}\n")
        try:
            folder_name = "startup-advisor-" + str(uuid.uuid4())
            result = startup_advisor.invoke_with_tasks([
                            research_task, marketing_strategy_task, 
                            campaign_idea_task, copy_creation_task,
                            final_edit_task
                        ],
                        additional_instructions=dedent(f"""
                Since you have a long and complex process, please save intermediate results of tasks to files
                as you complete them. Do NOT wait until the end to save the content.
                Intermediate results help drive follow-up work on detailed implementation and influence future iterations 
                of the strategy and campaigns. Use bucket {inputs['bucket']} for storage, and use folder {folder_name}.
                When you are done with all the tasks and summarizing results, do share the names of the files that you 
                saved for each task, so that they can be more easily retrieved later.
                                    """),
                        processing_type="sequential", 
                        enable_trace=True, trace_level=args.trace_level)
            print(result)
        except Exception as e:
            print(e)
            traceback.print_exc()
            pass

        duration = datetime.datetime.now() - time_before_call
        print(f"\nTime taken: {duration.total_seconds():,.1f} seconds")
    else:
        print("Recreated agents.")


if __name__ == '__main__':

    default_inputs = {
        'customer_domain': 'flyingCars.com',
        'project_description': dedent("""
FlyingCars, wants to be the leading supplier of flying cars. 
The project is to build an innovative marketing strategy to showcase FlyingCars advanced 
offerings, emphasizing ease of use, cost effectiveness, productivity, and safety. 
Target high net worth individuals, highlighting success stories and transformative 
potential. Be sure to include a draft for a 30-second video ad.
""")
    }    

    parser = argparse.ArgumentParser()

    parser.add_argument("--recreate_agents", required=False, default=True, help="False if reusing existing agents.")
    parser.add_argument("--bucket", required=False, default="<ENTER-S3-BUCKET-NAME>", help="s3 bucket to use for interim and final results.")
    parser.add_argument("--web_domain", required=False, 
                        default=default_inputs['customer_domain'],
                        help="The web domain name for the project (e.g., AnyCompany.ai).")
    parser.add_argument("--project", required=False, 
                        default=default_inputs['project_description'],
                        help="The project that needs a marketing strategy.")
    parser.add_argument("--trace_level", required=False, default="core", help="The level of trace, 'core', 'outline', 'all'.")
    
    args = parser.parse_args()
    main(args)
