#!/usr/bin/env python

import sys
sys.path.insert(0, '..')
sys.path.insert(1, '../..')

import datetime
import traceback
import argparse
import yaml

from bedrock_helpers import Agent, SupervisorAgent, Task, region, account_id

def create_agent(agent_name, agent_content, tools=None):
    agent = Agent(agent_name, agent_content, tools)
    print(f"Created agent: {agent_name}")
    return agent

def main(args):
    if args.recreate_agents == "false":
        Agent.set_force_recreate_default(False)
    else:
        Agent.set_force_recreate_default(True)

    inputs = {
        'origin': 'Boston, BOS',
        'destination': 'New York, JFK',
        'age': 25,
        'hotel_location': 'Times Square',
        'arrival': 'Dec 26, 11:00',
        'departure': 'Jan 1, 17:00',
    }


    with open('tasks.yaml', 'r') as file:
        yaml_task_content = yaml.safe_load(file)

    activity_planning_task = Task('activity_planning_task', yaml_task_content, inputs)
    restaurant_scout_task = Task('restaurant_scout_task', yaml_task_content, inputs)
    itinerary_compilation_task = Task('itinerary_compilation_task', yaml_task_content, inputs)


    with open('agents.yaml', 'r') as file:
        yaml_agent_content = yaml.safe_load(file)

    activity_finder = Agent('activity_finder', yaml_agent_content,
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
    restaurant_scout = Agent('restaurant_scout', yaml_agent_content,
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
    itinerary_compiler = Agent('itinerary_compiler', yaml_agent_content)
    

    print("\n\nCreating supervisor agent...\n\n")
    trip_planner = SupervisorAgent("trip_planner", yaml_agent_content,
                                 [activity_finder, restaurant_scout, itinerary_compiler])
    
    if args.recreate_agents == "false":
        print("\n\nInvoking supervisor agent...\n\n")

        time_before_call = datetime.datetime.now()
        print(f"time before call: {time_before_call}\n")
        try:
            print(trip_planner.invoke_with_tasks([
                        activity_planning_task, restaurant_scout_task, itinerary_compilation_task
                    ],
                    additional_instructions="For the final response, please only return the final itinerary.",
                    processing_type="sequential", 
                    enable_trace=True, trace_level=args.trace_level))
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
    parser.add_argument("--recreate_agents", required=False, default=True, help="False if reusing existing agents.")
    parser.add_argument("--trace_level", required=False, default="core", help="The level of trace, 'core', 'outline', 'all'.")
    args = parser.parse_args()
    
    main(args)
