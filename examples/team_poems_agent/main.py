#!/usr/bin/env python

import argparse
import yaml
import datetime
import sys

sys.path.insert(0, '.')
sys.path.insert(1, '../..')

from utils.bedrock_multi_agent_helper import Agent, SupervisorAgent, Task, account_id, region
import uuid

nhl_teams = [
    "Arizona Coyotes",
    "Boston Bruins",
    "Buffalo Sabres",
    "Carolina Hurricanes",
    "Chicago Blackhawks",
    "Columbus Blue Jackets",
    "Dallas Stars",
    "Detroit Red Wings",
    "Florida Panthers",
    "Montreal Canadiens",
    "Nashville Predators",
    "New Jersey Devils",
    "New York Islanders",
    "New York Rangers",
    "Ottawa Senators",
    "Philadelphia Flyers",
    "Pittsburgh Penguins",
    "St. Louis Blues",
    "Tampa Bay Lightning",
    "Toronto Maple Leafs",
    "Vancouver Canucks",
    "Vegas Golden Knights",
    "Washington Capitals",
    "Winnipeg Jets"
]

nfl_teams = [
    "Arizona Cardinals",
    "Atlanta Falcons",
    "Baltimore Ravens",
    "Buffalo Bills",
    "Carolina Panthers",
    "Chicago Bears",
    "Cincinnati Bengals",
    "Cleveland Browns",
    "Dallas Cowboys",
    "Denver Broncos",
    "Detroit Lions",
    "Green Bay Packers",
    "Houston Texans",
    "Indianapolis Colts",
    "Jacksonville Jaguars",
    "Kansas City Chiefs",
    "Las Vegas Raiders",
    "Los Angeles Chargers",
    "Los Angeles Rams",
    "Miami Dolphins",
    "Minnesota Vikings",
    "New England Patriots",
    "New Orleans Saints",
    "New York Giants",
    "New York Jets",
    "Philadelphia Eagles",
    "Pittsburgh Steelers",
    "San Francisco 49ers",
    "Seattle Seahawks",
    "Tampa Bay Buccaneers",
    "Tennessee Titans",
    "Washington Commanders"
]

def main(args):
    inputs = {
        "team_name": args.team_name, 
        "number_of_fun_facts": 3
    }
    
    if args.recreate_agents == "false":
        Agent.set_force_recreate_default(False)
    else:
        Agent.set_force_recreate_default(True)

    with open('tasks.yaml', 'r') as file:
        yaml_content = yaml.safe_load(file)

    number_of_championships_task = Task('number_of_championships_task', yaml_content, inputs)
    fun_facts_task = Task('fun_facts_task', yaml_content, inputs)
    famous_player_task = Task('famous_player_task', yaml_content, inputs)
    team_poem_task = Task('team_poem_task', yaml_content, inputs)

    # make an array of arrays of tasks, each array entry will have an array of 
    # tasks that use a particular NFL team name
    tasks_for_every_team = []
    all_teams = nhl_teams + nfl_teams
    for team in all_teams:
        tmp_inputs = {"team_name": team, "number_of_fun_facts": 3}
        tasks_for_every_team.append([
            Task('number_of_championships_task', yaml_content, tmp_inputs),
            Task('fun_facts_task', yaml_content, tmp_inputs),
            Task('famous_player_task', yaml_content, tmp_inputs),
            Task('team_poem_task', yaml_content, tmp_inputs)
        ])

    with open('agents.yaml', 'r') as file:
        yaml_content = yaml.safe_load(file)
    
    sports_research_agent = Agent('sports_research_agent', 
                                    yaml_content,
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
    sports_poetry_writer = Agent('sports_poetry_writer', yaml_content)

    print("\n\nCreating supervisor agent...\n\n")

    sports_team_poet = SupervisorAgent("sports_team_poet", yaml_content,
                                    [sports_research_agent,
                                    sports_poetry_writer])
        
    if args.recreate_agents == "false":
        input_text = f"Do some research to bring me 2 fun facts about the {args.team_name}."
        print(f"\n\nAsking supervisor agent a simple question it should route immediately: \n{args.team_name}\nInvoking...\n\n")

        time_before_call = datetime.datetime.now()
        print(f"time before call: {time_before_call}\n")

        one_conversation = str(uuid.uuid4())
        print(sports_team_poet.invoke(input_text,
                                      session_id=one_conversation,
                                    enable_trace=True, trace_level=args.trace_level))

        duration = datetime.datetime.now() - time_before_call
        print(f"\nTime taken: {duration.total_seconds():,.1f} seconds")

        time_before_call = datetime.datetime.now()
        print(f"time before call: {time_before_call}\n")

        print("\n\n\nNow asking a follow-up to be sure the routing continues with the same sub-agent...")
        input_text = f"And who is their most famous player?."
        print(f"Follow-up: {input_text}...")

        print(sports_team_poet.invoke(input_text,
                                      session_id=one_conversation,
                                    enable_trace=True, trace_level=args.trace_level))

        duration = datetime.datetime.now() - time_before_call
        print(f"\nTime taken: {duration.total_seconds():,.1f} seconds")

        print("\n\n\nNow giving a new request in a new session, with a request that must span sub-agents, falls back to supervisor vs classifier")
        input_text = f"Do some research to include 2 fun facts about the {args.team_name}. Then use those facts in a poem."
        print(f"\n\nAsking supervisor agent the following: \n{input_text}\nInvoking...\n\n")

        time_before_call = datetime.datetime.now()
        print(f"time before call: {time_before_call}\n")

        print(sports_team_poet.invoke(input_text,
                                    enable_trace=True, trace_level=args.trace_level))

        duration = datetime.datetime.now() - time_before_call
        print(f"\nTime taken: {duration.total_seconds():,.1f} seconds")


        print("\n\n\nNow invoking supervisor agent with a set of tasks...\n\n")

        time_before_call = datetime.datetime.now()
        print(f"time before call: {time_before_call}\n")

        print(sports_team_poet.invoke_with_tasks([
                            number_of_championships_task, fun_facts_task, 
                            famous_player_task, team_poem_task
                        ],
                    additional_instructions="For the final response, pls only return the actual poem.",
                    processing_type="sequential", 
                    enable_trace=True, trace_level=args.trace_level))

        duration = datetime.datetime.now() - time_before_call
        print(f"\nTime taken: {duration.total_seconds():,.1f} seconds")
    else:
        print("Recreated agents.")

    return 

    # Make the same invoke_with_tasks call, but do it with N threads in parallel
    number_of_parallel_threads = len(all_teams) // 4

    print(f"\n\nInvoking supervisor agent with {number_of_parallel_threads} threads...\n\n")
    time_before_call = datetime.datetime.now()
    print(f"time before call: {time_before_call}\n")

    # Make a pool of threads and run the invoke_with_tasks call in parallel
    from multiprocessing.dummy import Pool as ThreadPool
    pool = ThreadPool(number_of_parallel_threads)

    # use the thread pool to create a poem for each and every NFL team using
    # the array of tasks lists in every_team_tasks
    results = pool.map(lambda tasks: sports_team_poetry_agent.invoke_with_tasks(tasks,
                additional_instructions="For the final response, pls only return the actual poem.",
                processing_type="sequential", #"allow_parallel", #"sequential",
                enable_trace=False, trace_level="core"), tasks_for_every_team)
                                    
    duration = datetime.datetime.now() - time_before_call   
    pool.close()

    print(f"\n\nTime taken: {duration.total_seconds():,.1f} seconds to process {len(tasks_for_every_team)} team poetry processes in parallel.")

    # Print the results

    print("\n\n\n***** Results: *****\n\n")
    result_num = 1
    for result in results:
        curr_team = all_teams[result_num - 1]
        print(f"--- Poem for {curr_team} ({result_num}) ---")
        print(f"{result[0:]}\n\n")
        result_num += 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--recreate_agents", 
                        required=False, default=True, 
                        help="False if reusing existing agents.")
    parser.add_argument("--team_name", required=False, 
                        default="New England Patriots",
                        help="Name of the sports team for your poem.")
    parser.add_argument("--trace_level", required=False, default="core", help="The level of trace, 'core', 'outline', 'all'.")
    args = parser.parse_args()
    main(args)
