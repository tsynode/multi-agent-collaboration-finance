#!/usr/bin/env python

import datetime
import argparse
import sys

sys.path.insert(0, ".")
sys.path.insert(1, "../..")

from src.utils.bedrock_agent import Agent, SupervisorAgent, Task, account_id


def main(args):
    # User input for travel preferences
    user_input = {
        "voyage": args.voyage,
    }

    if args.recreate_agents == "false":
        Agent.set_force_recreate_default(False)
    else:
        Agent.set_force_recreate_default(True)

    # Define the Task
    travel_recommendation_task = Task.direct_create(
        "travel_recommendation_task",
        description=f"Research and recommend suitable travel destinations based on the user's dream vacation: {user_input['voyage']}",
        expected_output="A list of recommended destinations with brief descriptions.",
        inputs=user_input,
    )

    # Define the Agent
    travel_agent = Agent.direct_create(
        "travel_agent",
        role="Travel Destination Researcher",
        goal="Find destinations matching user preferences",
        tool_code=f"arn:aws:lambda:{args.region}:{account_id}:function:websearch_lambda",
        tool_defs=[
            {
                "name": "web_search",
                "description": "Searches the web for information",
                "parameters": {
                    "search_query": {
                        "description": "The query to search the web with",
                        "type": "string",
                        "required": True,
                    },
                    "target_website": {
                        "description": "The specific website to search including its domain name. If not provided, the most relevant website will be used",
                        "type": "string",
                        "required": False,
                    },
                    "topic": {
                        "description": "The topic being searched. 'news' or 'general'. Helps narrow the search when news is the focus.",
                        "type": "string",
                        "required": False,
                    },
                    "days": {
                        "description": "The number of days of history to search. Helps when looking for recent events or news.",
                        "type": "string",
                        "required": False,
                    },
                },
            }
        ],
    )

    voyage_virtuoso = SupervisorAgent.direct_create(
        "voyage_virtuoso",
        role="Voyage Virtuoso",
        goal="Plan the ultimate vacation for someone with a large budget given their preferences",
        collaboration_type="SUPERVISOR",
        instructions="""
                                Act as a travel agent specializing in high end exoctic vacation planning.
                                Budget is not in your vocabulary, as the sky is the limit. The more exotic the better.
                                Take a simple description of the desired voyage, do some research on it,
                                and generate some cool options and a recommendation for which one is preferred, with some 
                                explanation of your reasoning.""",
        collaborator_agents=[
            {
                "agent": "travel_agent",
                "instructions": """
                                    Use this collaborator for doing research about destinations and for
                                    generating options and recommendations.""",
                "relay_conversation_history": "DISABLED",
            }
        ],
        collaborator_objects=[travel_agent],
    )

    if args.recreate_agents == "false":
        time_before_call = datetime.datetime.now()
        print(f"time before call: {time_before_call}\n")

        result = voyage_virtuoso.invoke_with_tasks(
            [travel_recommendation_task],
            processing_type="sequential",
            enable_trace=True,
            trace_level=args.trace_level,
        )
        print(result)

        duration = datetime.datetime.now() - time_before_call
        print(f"\nTime taken: {duration.total_seconds():,.1f} seconds")
    else:
        print("Recreated agents.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--recreate_agents",
        required=False,
        default=True,
        help="False if reusing existing agents.",
    )
    parser.add_argument(
        "--region",
        required=False,
        default="us-west-2",
        help="The region to use for cloud resources.",
    )
    parser.add_argument(
        "--trace_level",
        required=False,
        default="core",
        help="The level of trace, 'core', 'outline', 'all'.",
    )
    parser.add_argument(
        "--voyage",
        required=False,
        help="Brief description of the amazing voyage you want to take",
        default="Give me some great options for skip trip for an expert and with ski-on/ski-off townhouse",
    )
    args = parser.parse_args()
    main(args)
