# Multi-agents for process automation

Amazon Bedrock multi-agent collaboration enables unfied conversational experiences
as well as new ways to deliver complex process automation. Companies now have a modular,
secure, and scalable way to leverage a collection of specialized AI agents to adress more 
complicated scenarios. Development teams can independently build AI agents with deep expertise 
at a very specific set of outcomes, and these agents can be flexibly assembled into a multi-agent
system to execute a set of tasks. Supervisor agents dynamically plan and execute
across their available collaborators and knowledge bases, completing complex requests.
This addresses the scalability challenges of single-agent systems by allowing greater 
accuracy without the complexity associated with more complicated coding and prompt engineering.
Multi-level agent hierarchies are also supported, and agent processing can be both sequential and 
parallel. Bedrock agent tracing gives you the transparency needed for auditing and troubleshooting
multi-agent flows by giving step by step information about the chain of agent calls, and 
the inputs and outputs to every sub-agent and tool along the way.

## Purpose of this repo

This repo is designed to get you started with Bedrock Agents multi-agent collaboration by providing a
set of examples that demonstrate how it works and showcases some of its core capabilities. The
field of multi-agent systems is still in the early days, and our goal is to give you some off the
shelf starter examples that inspire you as you being to tackle real world scenarios.

## Examples

To get you started working with Bedrock multi-agent processes, we provide the following examples:

- **Voyage Vituoso.** Dream big with the Voyage Virtuoso, a supervisor agent that is built for high net worth individuals that need help picking the
most expensive and elaborate destinations given a theme ("I want to ski on expert slopes, but need ski-on/ski-off resort with great night life").
- **Portfolio Assistant.** This supervisor agent has two collaborators, a News agent and a Stock Data agent. Those specialists are orchestrated to perform investment analysis for a given stock ticker based on the latest news and recent stock price movements. 
- **Sports Team Poet.** This is a fun example for sports fans. The Sports Team Poet is a supervisor with a Research Agent and a Sports Poetry Writer. Pick your favorite team (go Celtics!) and see multi-agents collaborate to conduct web research about your team and make a fun poem with those insights. Have fun!
- **Trip Planner.** The Trip Planner uses a few sub-agents to help you build a robust itinerary given a destination and number of days. It leverages a Restaurant Scout and an Activity Finder to get great ideas, and an Intinerary Compiler to finish the job. Try it out for your next trip.
- **Startup Advisor.** Have a new startup in mind, but haven't quite hired your marketing staff? Use this supervisor to do your market research, come up with campaign ideas, and write effective campaign copy. It uses a set of 5 sub-agents to get the job done (Market Analyst, Content Creator, ...).

## Getting started

To make these examples more interesting and powerful, they all have a dependency on a web search tool. You'll
need to set that up before you run them. A cloud formation template is provided, and the instructions are straightforward.
You'll need an API key for the underlying search API, and that supports a free tier.
