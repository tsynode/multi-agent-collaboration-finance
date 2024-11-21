#!/usr/bin/env python

import datetime
import argparse
import sys

sys.path.insert(0, '.')
sys.path.insert(1, '../..')

from bedrock_helpers import Tool, Agent, SupervisorAgent, Task

def main(args):
    # User input for travel preferences
    user_input = {
        "preferences": "I want a tropical beach vacation with great snorkeling and vibrant nightlife.",
        "region": "us-west-2"
    }

    if args.recreate_agents == "false":
        Agent.set_force_recreate_default(False)
    else:
        Agent.set_force_recreate_default(True)

    web_search_tool = Tool({
            "code": f"arn:aws:lambda:{user_input['region']}:355151823911:function:websearch_lambda",
            "definition": { 
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
            }
        }
    )

    # Define the Task
    travel_recommendation_task = Task.direct_create("travel_recommendation_task",
        description=f"Based on the user's travel preferences: {user_input['preferences']}, research and recommend suitable travel destinations.",
        expected_output="A list of recommended destinations with brief descriptions.",
        inputs=user_input
    )

    # Define the Agent
    travel_agent = Agent.direct_create("travel_agent",
                    role="Travel Destination Researcher",
                    goal="Find dream destinations matching user preferences",
                    backstory="You are an experienced travel agent specializing in personalized travel recommendations.",
                    tools=[web_search_tool] 
    )

    supervisor_description = """
    You are a Supervisor Agent that plans and executes multi step tasks based on user input.
    To accomplish those tasks, you delegate your work to a sub-agent or knowledge base.
    """ 
    supervisor_instructions = """"""

    dream_trip_agent = SupervisorAgent("dream_trip_agent", 
                                [travel_agent],
                                supervisor_instructions,
                                supervisor_description)

    if args.recreate_agents == "false":
        time_before_call = datetime.datetime.now()
        print(f"time before call: {time_before_call}\n")

        result = dream_trip_agent.invoke_with_tasks([travel_recommendation_task], 
                                                processing_type="sequential", 
                                                enable_trace=False, 
                                                trace_level=args.trace_level)
        print(result)

        duration = datetime.datetime.now() - time_before_call
        print(f"\nTime taken: {duration.total_seconds():,.1f} seconds")
    else:
        print("Recreated agents.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--recreate_agents", required=True, help="False if reusing existing agents.")
    parser.add_argument("--trace_level", required=False, default="core", help="The task to perform.")
    args = parser.parse_args()
    main(args)
