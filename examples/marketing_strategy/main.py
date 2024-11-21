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

from bedrock_helpers import Agent, SupervisorAgent, Task, Tool

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

#     inputs = {
#         'customer_domain': 'flyingCars.com',
#         'project_description': dedent("""
# FlyingCars, wants to be the leading supplier of flying cars. 
# The project is to build an innovative marketing strategy to showcase FlyingCars advanced 
# offerings, emphasizing ease of use, cost effectiveness, productivity, and safety. 
# Target high net worth individuals, highlighting success stories and transformative 
# potential. Be sure to include a draft for a 30-second video ad.
# """),
#         'bucket': args.bucket
#     }    

    with open('tasks.yaml', 'r') as file:
        yaml_content = yaml.safe_load(file)

    research_task = Task('research_task', yaml_content, inputs)
    project_understanding_task = Task('project_understanding_task', yaml_content, inputs)
    marketing_strategy_task = Task('marketing_strategy_task', yaml_content, inputs)
    campaign_idea_task =  Task('campaign_idea_task', yaml_content, inputs)
    copy_creation_task = Task('copy_creation_task', yaml_content, inputs)

    with open('tools.yaml', 'r') as file:
        yaml_tool_content = yaml.safe_load(file)
        
    web_search_tool = Tool(yaml_tool_content['web_search'])
    save_file_tool = Tool(yaml_tool_content['save_file'])
    get_file_tool = Tool(yaml_tool_content['get_file'])
    
    with open('marketing_strategy.yaml', 'r') as file:
        yaml_content = yaml.safe_load(file)

    lead_market_analyst = Agent('lead_market_analyst', yaml_content,
                                tools=[web_search_tool])
    chief_marketing_strategist = Agent('chief_marketing_strategist', 
                                    yaml_content,
                                    tools=[web_search_tool])
    creative_content_creator = Agent('creative_content_creator', yaml_content)
    agent_state_storage_agent = Agent('agent_state_storage_agent', 
                                      yaml_content,
                                      tools=[save_file_tool, 
                                             get_file_tool])
    
    supervisor_description = """
    You are a Supervisor Agent that plans and executes multi step tasks based on user input.
    To accomplish those tasks, you delegate your work to a sub-agent or knowledge base.
    """ 
    supervisor_instructions = """"""
    # You are a Supervisor Agent that plans and executes multi step tasks based on user input.
    # To accomplish those tasks, you delegate your work to a sub-agent, but you never reveal 
    # to the user that you are using sub-agents.
    # Pretend that you are handling all the requests directly. When sending a request to 
    # a sub-agent, be as explicit as possible about what you need it to do and 
    # provide specific context to help it do its job as an expert at that particular task.
    # """ 
    
    print("\n\nCreating marketing_strategy_agent as a supervisor agent...\n\n")
    marketing_strategy_agent = SupervisorAgent("marketing_strategy_agent", 
                                [lead_market_analyst, 
                                chief_marketing_strategist, 
                                creative_content_creator, 
                                agent_state_storage_agent],
                                supervisor_instructions, 
                                supervisor_description)
    
    if args.recreate_agents == "false":
        print("\n\nInvoking supervisor agent...\n\n")

        time_before_call = datetime.datetime.now()
        print(f"time before call: {time_before_call}\n")
        try:
            folder_name = "marketing-strategy-" + str(uuid.uuid4())
            result = marketing_strategy_agent.invoke_with_tasks([
                        research_task, project_understanding_task, marketing_strategy_task, 
                        campaign_idea_task,
                        copy_creation_task
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--recreate_agents", required=True, help="False if reusing existing agents.")
    parser.add_argument("--bucket", required=True, help="s3 bucket to use for interim and final results.")
    parser.add_argument("--web_domain", required=False, 
                        default="sports.ai",
                        help="The project that needs a marketing strategy.")
    parser.add_argument("--project", required=False, 
                        default=dedent("""
SportsAI, a leading provider of sports analytics, aims to revolutionize analytics for collegiate and professional sports teams. 
This project involves developing an innovative marketing strategy to showcase SportsAI's advanced AI-driven solutions, 
emphasizing ease of use, scalability, and accuracy. The campaign will target tech-savvy decision-makers in collegiate basketball teams, 
highlighting success stories and the transformative potential of SportsAI's platform.
"""),
                        help="The project that needs a marketing strategy.")
    parser.add_argument("--trace_level", required=False, default="core", help="The task to perform.")
    args = parser.parse_args()
    main(args)
