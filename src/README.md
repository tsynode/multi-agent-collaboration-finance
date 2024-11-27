<h2 align="center">Amazon Bedrock Multi-Agent Collaboration&nbsp;</h2>

Amazon Bedrock multi-agent collaboration enables unfied conversational experiences as well as new ways to deliver complex process automation. Customers now have a modular, secure, and scalable way to leverage a collection of specialized AI agents to adress more complicated scenarios. Development teams can independently build AI agents with deep expertise at a very specific set of outcomes, and these agents can be flexibly assembled into a multi-agent nsystem to execute a set of tasks. Supervisor agents dynamically plan and execute across their available collaborators and knowledge bases, completing complex requests. This addresses the scalability challenges of single-agent systems by allowing greater accuracy without the complexity associated with more complicated coding and prompt engineering. Multi-level agent hierarchies are also supported, and agent processing can be both sequential and parallel. Bedrock agent tracing gives you the transparency needed for auditing and troubleshooting multi-agent flows by giving step by step information about the chain of agent calls, and the inputs and outputs to every sub-agent and tool along the way.

## �� Table of Contents ��

- [Prerequisites](#prerequisites)
- [Build Amazon Bedrock Multi-Agent Collaboration using boto3](#build-amazon-bedrock-multi-agent-collaboration-using-boto3)
- [Build Amazon Bedrock Multi-Agent Collaboration using [bedrock_agent.py](/src/utils/bedrock_agent.py)](#build-amazon-bedrock-multi-agent-collaboration-using-bedrock_agent.py)

## Prerequisites

- AWS Account with Bedrock access
- Python 3.8 or later
- Required Python packages (specified in [`requirements.txt`](/requirements.txt))

Make sure to run the following commands:

```
git clone https://github.com/aws-samples/bedrock-multi-agents-collaboration-workshop

cd bedrock-multi-agents-collaboration-workshop

python3 -m venv .venv

source .venv/bin/activate

pip3 install -r src/requirements.txt
```

> [!TIP]   
> Run the `deactivate` command to deactivate the virtual environment.

## Build Amazon Bedrock Multi-Agent Collaboration using boto3
<p align="center">
  <a href="/src/examples/energy_efficiency_management_agent/"><img src="https://img.shields.io/badge/Example-Energy_Efficiency_Management_Agent-blue" /></a>
  <a href="/src/examples/devops_agent/"><img src="https://img.shields.io/badge/Example-DevOps_Agent_Agent-blue" /></a>
</p>


## Build Amazon Bedrock Multi-Agent Collaboration using [bedrock_agent.py](/src/utils/bedrock_agent.py)

<p align="center">
  [![Static Badge](https://img.shields.io/badge/Example-00_Hello_World_Agent-blue)](/src/examples/00_hello_world_agent/)
  [![Static Badge](https://img.shields.io/badge/Example-Portfolio_Assistant_Agent-blue)](/src/examples/devops_agent/)
</p>