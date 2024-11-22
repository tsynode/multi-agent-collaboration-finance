#!/usr/bin/env python

import sys

sys.path.insert(0, '.')
sys.path.insert(1, '../..')

from bedrock_helpers import Tool, Agent, SupervisorAgent, Task

def main():
    Agent.set_force_recreate_default(False)

    inputs = {'ticker': 'AMZN'} # 'AAPL'} #

    # web_search_tool = Tool({
    #         "code": "arn:aws:lambda:us-east-1:355151823911:function:websearch_lambda",
    #         "definition": { 
    #             "name": "web_search", 
    #             "description": "Searches the web for information", 
    #             "parameters": {
    #                 "search_query": {
    #                     "description": "The query to search the web with",
    #                     "type": "string",
    #                     "required": True},
    #                 "target_website": {
    #                     "description": "The specific website to search including its domain name. If not provided, the most relevant website will be used",
    #                     "type": "string", "required": False}
    #                 }
    #             }
    # })

    # stock_data_tool = Tool({
    #         "code": "arn:aws:lambda:us-east-1:355151823911:function:stock_data_lookup",
    #         "definition": { 
    #             "name": "stock_data_lookup", 
    #             "description": "Gets the 1 month stock price history for a given stock ticker, formatted as JSON", 
    #             "parameters": {
    #                 "ticker": {
    #                     "description": "The ticker to retrieve price history for",
    #                     "type": "string",
    #                     "required": True}
    #                 }
    #             }
    # })

    # Define News Agent
    news_agent = Agent.direct_create(
        name="news_agent",
        role='Market News Researcher',
        goal='Fetch latest relevant news for a given stock based on ticker.',
        backstory='Top researcher in financial markets and company announcements.',
        # tools=[web_search_tool]  
    )

    # Define Stock Data Agent
    # stock_data_agent = Agent.direct_create(
    #     name="stock_data_agent",
    #     role="Financial Data Collector",
    #     goal="Retrieve accurate stock trends for {ticker}.",
    #     backstory="Specialist in real-time financial data extraction.",
    #     tools=[stock_data_tool]
    # )

    # Define Analyst Agent
    analyst_agent = Agent.direct_create(
        name="analyst_agent",
        role='Financial Analyst',
        goal='Analyze stock trends and market news to generate insights.',
        backstory='Experienced analyst providing strategic recommendations.',
    )

    # Create Tasks
    news_task = Task.direct_create(
        name="news_task",
        description='Retrieve latest news about the given stock ticker: {ticker}.',
        expected_output='List of 5 relevant news articles.',
        inputs=inputs
    )

    # stock_data_task = Task.direct_create(
    #     name="stock_data_task",
    #     description='Retrieve stock price history for the given stock ticker: {ticker}.',
    #     expected_output='JSON object containing stock price history.',
    #     inputs=inputs
    # )

    analysis_task = Task.direct_create(
        name="analysis_task",
        # description=("""
        #     Analyze the news and stock trends, 
        #     to provide actionable insights on {ticker}, 
        #     including news highlights and recommendations for the future.
        #     """
        # ),
        description=("""
            Analyze the stock trends, 
            to provide actionable insights on {ticker}, 
            including recommendations for the future.
            """
        ),
        expected_output='A summary report with market trends and insights.',
        inputs=inputs
    )

    supervisor_description = """
    You are a Supervisor Agent that plans and executes multi step tasks based on user input.
    To accomplish those tasks, you delegate your work to a sub-agent or knowledge base.""" 

    supervisor_instructions = """You are a Supervisor Agent that plans and executes multi step tasks based on user input.
    To accomplish those tasks, you delegate your work to a sub-agent, but you never reveal to the user that you are using sub-agents.
    Pretend that you are handling all the requests directly. When sending a request to a sub-agent,
    be as explicit as possible about what you need it to do and provide specific context to help it do its
    job as an expert at that particular task.
    If topics outside of the sub-agents capabilities are asked, please respond back the customer with I'm sorry I can only cover mortgage related topics.
    note that a sub-agent may be capable of asking for specific additional info, so don't feel obligated to ask the user for 
    input before you delegate work to a sub-agent. If a sub-agent is asking for additional information, 
    ask the user for that, but do not reveal that you are using a sub-agent. For example, If any sub-agent asks 
    for a customer id, just ask the user for the customer id without saying that the sub-agent asked for it.
    """ 
    stock_analysis_agent = SupervisorAgent("stock_analysis_agent", 
                                 [#news_agent, 
                                #   stock_data_agent, 
                                  analyst_agent],
                                  supervisor_instructions, supervisor_description)
    
    result = stock_analysis_agent.invoke_with_tasks([
                # stock_data_task, 
                # news_task, 
                analysis_task],
                processing_type="sequential", 
                enable_trace=True, 
                trace_level="all")
    print(result)

if __name__ == '__main__':
    main()

