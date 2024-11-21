import boto3 
import uuid
from typing import List, Dict
import time

print(f'boto3 version: {boto3.__version__}')

#Clients
s3_client = boto3.client('s3')
sts_client = boto3.client('sts')
bedrock_agent_client = boto3.client('bedrock-agent')
bedrock_agent_runtime_client = boto3.client('bedrock-agent-runtime')
bedrockruntime_client = boto3.client('bedrock-runtime')

from new_agent import AgentsForAmazonBedrock
# from agents import create_agent, associate_sub_agents #, list_agent_collaborators, invoke_agent_helper

agents_helper = AgentsForAmazonBedrock()

region = agents_helper.get_region()
account_id = sts_client.get_caller_identity()["Account"]

suffix = f"{region}-{account_id}"
bucket_name = f'mac-workshop-{suffix}'
agent_foundation_models = [ 
    "us.anthropic.claude-3-haiku-20240307-v1:0",
    "us.anthropic.claude-3-sonnet-20240307-v1:0",
    "us.anthropic.claude-3-5-sonnet-20240620-v1:0",
    "us.anthropic.claude-3-5-haiku-20241022-v1:0",
    "us.anthropic.claude-3-5-sonnet-20241022-v2:0"
    ]

DEFAULT_AGENT_MODEL = "us.anthropic.claude-3-5-haiku-20241022-v1:0"
DEFAULT_SUPERVISOR_MODEL = "anthropic.claude-3-5-sonnet-20240620-v1:0" #"us.anthropic.claude-3-5-sonnet-20241022-v2:0"

MAX_DESCR_SIZE = 200 # Due to max size enforced by Agents for description
    
class Tool: 
    def __init__(self, yaml_content: Dict):
        self.code = yaml_content['code']
        self.definition = yaml_content['definition']

        # Provide a default value for requireConfirmation
        if 'requireConfirmation' not in self.definition:
            self.definition['requireConfirmation'] = 'DISABLED'

    @classmethod
    def to_action_groups(cls, base_name: str, 
                        tools: List['Tool']):
        _action_groups = []
        _ag_num = 1
        for _tool in tools:
            _tmp_ag = {
                "actionGroupName": f"{base_name}_{_ag_num}",
                "actionGroupExecutor": {
                    "lambda": _tool.code
                },
                "description": _tool.definition['description'],
                "functionSchema": {
                    "functions": [_tool.definition]
                }
            }
            _action_groups.append(_tmp_ag)
            _ag_num += 1
        return _action_groups


    def __str__(self):
        return f"Code: {self.code}\nDefinition: {self.definition}"

# define a ToolCatalog class that takes a set of tools and gives
# an easy way to get one of them by name
class ToolCatalog:
    def __init__(self, yaml_content: Dict):
        self.tools = {}
        for tool_name, tool_data in yaml_content.items():
            self.tools[tool_name] = Tool(tool_data)

    def get_tool(self, tool_name: str) -> Tool:
        return self.tools[tool_name]

class Task:
    def __init__(self, name: str, yaml_content: Dict, inputs):
        self.name = name
        self.description = yaml_content[name]['description']
        # update the description to replace input vales for named inputs
        self.description = self.description.format(**inputs)
        self.expected_output = yaml_content[name]['expected_output']
        if 'output_type' in yaml_content[name]:
            self.output_type = yaml_content[name]['output_type']
        else:
            self.output_type = None

    @classmethod
    def direct_create(cls, name: str, description: str, expected_output: str, inputs: Dict):
        return cls(name, {name: {'description': description, 'expected_output': expected_output}}, inputs)

    def __str__(self):
        if self.output_type is not None:
            return f"{self.description} Expected output: {self.expected_output} Output type: {self.output_type}"
        else:
            return f"{self.description} Expected output: {self.expected_output}"

# define an Agent class that simply has a role, goal, and backstory
class Agent:
    default_force_recreate: bool=False

    @classmethod
    def set_force_recreate_default(cls, force_recreate: bool):
        Agent.default_force_recreate = force_recreate

    def __init__(self, name, yaml_content, tools: List[Tool]=None, 
                 llm: str=None,
                 verbose: bool=False):
        self.name = name

        self.role = yaml_content[name]['role']
        self.goal = yaml_content[name]['goal']
        self.backstory = yaml_content[name]['backstory']
        self.agent_id = None 
        self.agent_alias_id = None
        self.agent_alias_arn = None 
        self.instructions = ""

        if 'code_interpreter' in yaml_content[name]:
            self.code_interpreter = yaml_content[name]['code_interpreter']
        else:
            self.code_interpreter = False

        if 'additional_function_iam_policy' in yaml_content[name]:
            tmp_policy_filename = yaml_content[name]['additional_function_iam_policy']
            with open(tmp_policy_filename, 'r') as file:
                self.additional_function_iam_policy = file.read()
        else:
            self.additional_function_iam_policy = None

        if 'tool_code' in yaml_content[name] and 'tool_defs' in yaml_content[name]:
            self.tool_code = yaml_content[name]['tool_code']
            self.tool_defs = yaml_content[name]['tool_defs']
        else:
            self.tool_code = None
            self.tool_defs = None

        if 'llm' in yaml_content[name]:
            self.llm = yaml_content[name]['llm']
        elif llm is not None:
            self.llm = llm
        else:
            self.llm = DEFAULT_AGENT_MODEL
        
        if not Agent.default_force_recreate:
            # if the agent already exists, get its agent_id and move on.
            try:
                self.agent_id = agents_helper.get_agent_id_by_name(self.name)
                self.agent_alias_id = agents_helper.get_agent_latest_alias_id(self.agent_id)
            except Exception as e:
                print(f"{e}")
                print(f"Agent {self.name} does not exist. Must force creation using force_recreate flag.")
                pass
            return
        
        else:
            # first delete existing lambda and bedrock agent if found
            print(f"\nDeleting existing agent and corresponding lambda for: {self.name}...")
            try:
                agents_helper.delete_lambda(f"{self.name}_ag")
                agents_helper.delete_agent(self.name)
            except:
                pass
    
            # now create a new bedrock agent 
            print(f"Creating agent {self.name}...")

            self.instructions = f"Role: {self.role}\nGoal: {self.goal}\nBackstory: {self.backstory}"

            # add workaround in instructions, since default prompts can yield hallucinations for tool use calls
            # if self.tool_code is None and self.tool_defs is None:
            if tools is None and self.tool_code is None and self.tool_defs is None:
                self.instructions += "\nYou have no available tools. Rely only on your own knowledge."

            (self.agent_id,
            self.agent_alias_id,
            self.agent_alias_arn) = agents_helper.create_agent(
                self.name, self.backstory[0:MAX_DESCR_SIZE-1], self.instructions, 
                [self.llm], code_interpretation=self.code_interpreter, 
                verbose=verbose)
            
            print(f"\nCreated agent, id: {self.agent_id}, alias id: {self.agent_alias_id}, alias arn: {self.agent_alias_arn}\n")

            # Add tools as Lamda or ROC action groups to support the specified capabilities
            if tools is None and self.tool_code is not None and self.tool_code != "ROC":
                print(f"Adding action group with Lambda: {self.tool_code}...")
                # Also updated to capture the new alias ID and ARN.
                # (self.agent_alias_id,
                # self.agent_alias_arn) = 
                agents_helper.add_action_group_with_lambda(
                        self.name, 
                        f"{self.name}_ag", 
                        self.tool_code, 
                        self.tool_defs,
                        f"actions_{self.name}", 
                        f"Set of functions for {self.name}",
                        self.additional_function_iam_policy)
                
                agents_helper.wait_agent_status_update(self.agent_id)

                _agent_alias = agents_helper._bedrock_agent_client.create_agent_alias(
                    agentAliasName='with-code-ag', agentId=self.agent_id
                )
                self.agent_alias_id = _agent_alias['agentAlias']['agentAliasId']
                self.agent_alias_arn = _agent_alias['agentAlias']['agentAliasArn']

                agents_helper.wait_agent_status_update(self.agent_id)

            elif tools is None and self.tool_code == "ROC":
                print(f"Adding action group with Return of Control...")
                resp = agents_helper.add_action_group_with_roc(
                        self.agent_id,
                        self.tool_defs,
                        f"actions_{self.name}",
                        f"Set of functions for {self.name}")
            elif tools is not None:
                _tool_num = 1
                for _tool in tools:
                    print(f"Adding tool: {_tool}...")
                    print(f"Adding action group for tool: {str(_tool.definition['name'])}...")
                    resp = agents_helper.add_action_group_with_lambda(
                            self.name, 
                            f"{self.name}_ag", 
                            _tool.code, 
                            [_tool.definition],
                            f"actions_{_tool_num}_{self.name}", 
                            f"Set of functions for {self.name}",
                            self.additional_function_iam_policy)
                    _tool_num += 1

                agents_helper.wait_agent_status_update(self.agent_id)
                
                _agent_alias = agents_helper._bedrock_agent_client.create_agent_alias(
                    agentAliasName='with-ags', agentId=self.agent_id
                )
                self.agent_alias_id = _agent_alias['agentAlias']['agentAliasId']
                self.agent_alias_arn = _agent_alias['agentAlias']['agentAliasArn']

                agents_helper.wait_agent_status_update(self.agent_id)

        # Make sure we have the final alias id saved.
        self.agent_alias_id = agents_helper.get_agent_latest_alias_id(self.agent_id)
        _old_alias_id = self.agent_alias_arn.split("/")[-1]
        self.agent_alias_arn = self.agent_alias_arn.replace(_old_alias_id, self.agent_alias_id)
        print(f"DONE: Agent: {self.name}, id: {self.agent_id}, alias arn: {self.agent_alias_arn}\n\n")
        
    @classmethod 
    # Return a session state populated with the files from the supplied list of filenames
    def add_file_to_session_state(cls, file_name, use_case='CODE_INTERPRETER', session_state=None):
        if use_case != "CHAT" and use_case != "CODE_INTERPRETER":
            raise ValueError("Use case must be either 'CHAT' or 'CODE_INTERPRETER'")
        if not session_state:
            session_state = {
                "files": []
            }
        type = file_name.split(".")[-1].upper()
        name = file_name.split("/")[-1]

        if type == "CSV":
            media_type = "text/csv" 
        elif type in ["XLS", "XLSX"]:
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        else:
            media_type = "text/plain"

        named_file = {
            "name": name,
            "source": {
                "sourceType": "BYTE_CONTENT", 
                "byteContent": {
                    "mediaType": media_type,
                    "data": open(file_name, "rb").read()
                }
            },
            "useCase": use_case
        }
        session_state['files'].append(named_file)

        return session_state

    @classmethod
    def direct_create(cls, name: str, role: str="", goal: str="", 
                backstory: str="", tools: List[Tool]=None,
                #  tool_code: str=None, tool_defs: List[Dict]=None, 
                llm: str=None):
        _yaml_content = {name: {'role': role, 'goal': goal, 'backstory': backstory}}
                                # 'tool_code': tool_code, 'tool_defs': tool_defs,
        if llm is not None:
            _yaml_content[name]['llm'] = llm
        return cls(name, _yaml_content, tools=tools)

    def invoke(self, input_text: str, session_id: str=str(uuid.uuid1()), 
               session_state: dict={}, enable_trace: bool=False, trace_level: str="none"):
        return agents_helper.invoke(input_text, self.agent_id, session_id=session_id,
                                    session_state=session_state,
                                    enable_trace=enable_trace, trace_level=trace_level)

    def invoke_roc(self, input_text: str, session_id: str=str(uuid.uuid1()), 
                   function_call: str=None, function_call_result: str=None,
                   enable_trace: bool=False):
        return agents_helper.invoke_roc(input_text, self.agent_id, session_id=session_id, 
                                        function_call=function_call,
                                        function_call_result=function_call_result,
                                        enable_trace=enable_trace)
    
    def invoke_roc_with_tools(self, input_text: str, tools_list=None, 
                              session_id: str=str(uuid.uuid1()),
                              enable_trace: bool=False,
                              trace_level: str="none"):
        roc_call = agents_helper.invoke_roc(input_text, self.agent_id, session_id=session_id,
                                            enable_trace=enable_trace) 
        invocation_inputs = roc_call['invocationInputs']
        for invocation_input in invocation_inputs:
            function_to_call = invocation_input["functionInvocationInput"]["function"]
            tool_args = {}
            for param in invocation_input["functionInvocationInput"]["parameters"]:
                tool_args[param["name"]] = param["value"]

            function_call_result = getattr(tools_list, function_to_call)(**tool_args)

            final_answer = self.invoke_roc("", 
                                           session_id=session_id,
                                           function_call=roc_call,
                                           function_call_result=function_call_result,
                                           enable_trace=enable_trace)
            return final_answer
   

# define a SupervisorAgent class that has a list of Agents, and some instructions
class SupervisorAgent:
    def __init__(self, name: str, sub_agents: List, instructions: str="", 
                 brief_description: str="", llm: str=None):
        self.name = name
        self.sub_agents = sub_agents
        self.instructions = instructions
        self.brief_description = brief_description
        self.supervisor_agent_id = None
        self.supervisor_agent_alias_id = None
        self.supervisor_agent_alias_arn = None

        # make an array called tmp_names with the names of each of the agents
        tmp_names = [agent.name for agent in sub_agents]

        _sub_agent_list = []
        for _sub_agent in sub_agents:
            _sub_agent_list.append({
                'sub_agent_alias_arn': _sub_agent.agent_alias_arn,
                'sub_agent_association_name': _sub_agent.name,
                'sub_agent_instruction': _sub_agent.instructions,
                'relay_conversation_history': 'DISABLED' #'TO_COLLABORATOR'
            })

        if not Agent.default_force_recreate:
            # if the supervisor agent already exists, get its agent_id and move on.
            try:
                self.supervisor_agent_id = agents_helper.get_agent_id_by_name(self.name)
                self.supervisor_agent_alias_id = agents_helper.get_agent_latest_alias_id(self.supervisor_agent_id)
            except:
                pass
            return

        # clean up existing supervisor if needed
        agents_helper.delete_lambda(f"{name}_lambda")
        agents_helper.delete_agent(name)

        # make the supervisor
        if llm is not None:
            self.llm = llm
        else:
            self.llm = DEFAULT_SUPERVISOR_MODEL

        # First create the supervisor agent.
        self.not_used = None 

        (self.supervisor_agent_id, 
        self.supervisor_agent_alias_id, 
        self.supervisor_agent_alias_arn) = agents_helper.create_agent(
            self.name,
            self.brief_description,
            self.instructions,
            model_ids=[self.llm],
            agent_collaboration='SUPERVISOR_ROUTER'
        )

        print(f"\nCreated supervisor, id: {self.supervisor_agent_id}, alias id: {self.supervisor_agent_alias_id}, alias arn: {self.supervisor_agent_alias_arn}\n")

        # Now associate the sub-agents
        self.supervisor_agent_alias_id, self.supervisor_agent_alias_arn = agents_helper.associate_sub_agents(
            self.supervisor_agent_id, _sub_agent_list
        )
        print(f"Associated sub-agents to supervisor: {self.name}...")
        print(f"Sub-agents: {_sub_agent_list}")
        print(f"Supervisor agent alias id: {self.supervisor_agent_alias_id}")
        print(f"Supervisor agent alias arn: {self.supervisor_agent_alias_arn}")

        # Make sure we have the final alias id saved.
        self.supervisor_agent_alias_id = agents_helper.get_agent_latest_alias_id(self.supervisor_agent_id)
        _old_alias_id = self.supervisor_agent_alias_arn.split("/")[-1]
        self.supervisor_agent_alias_arn = self.supervisor_agent_alias_arn.replace(_old_alias_id, self.supervisor_agent_alias_id)
        print(f"DONE: Agent: {self.name}, id: {self.supervisor_agent_id}, alias arn: {self.supervisor_agent_alias_arn}\n\n")


    def invoke(self, input_text: str, session_id: str=str(uuid.uuid1()), 
               enable_trace: bool=False, trace_level: str="none"):
        return agents_helper.invoke(input_text, self.supervisor_agent_id, 
                                    agent_alias_id=self.supervisor_agent_alias_id,
                                    session_id=session_id, 
                                    enable_trace=enable_trace,
                                    trace_level=trace_level)
    
    def invoke_with_tasks(self, tasks: list[Task], 
                          additional_instructions: str="",
                          processing_type: str="sequential", 
                          enable_trace: bool=False, trace_level: str="none",
                          verbose: bool=False):
        prompt = ''
        if processing_type == 'sequential':
            prompt += """
Please perform the following tasks sequentially. Be sure you do not
perform any of them in parallel. If a task will require information produced from a prior task, 
be sure to include the details as input to the task.\n\n"""
            task_num = 1
            for t in tasks:
                prompt += f"Task {task_num}. {t}\n"
                task_num += 1

            prompt += "\nBefore returning the final answer, review whether you have achieved the expected output for each task."

            if additional_instructions != "":
                prompt += f"\n{additional_instructions}"
        elif processing_type == "allow_parallel":
            prompt += """
Please perform as many of the following tasks in parallel where possible.
When a dependency between tasks is clear, execute those tasks in sequential order. 
If a task will require information produced from a prior task,
be sure to include the details as input to the task.\n\n"""
            task_num = 1
            for t in tasks:
                prompt += f"Task {task_num}. {t}\n"
                task_num += 1

            prompt += "\nBefore returning the final answer, review whether you have achieved the expected output for each task."

            if additional_instructions != "":
                prompt += f"\n{additional_instructions}"

        if verbose and enable_trace and trace_level == "core":
            print(f"Here is the prompt being sent to the supervisor:\n{prompt}\n")

        # make a session id with a prefix of current time to make the
        # id's sortable when looking at session logs or metrics or storage outputs.
        timestamp = int(time.time())
        session_id = self.name + "-" + str(timestamp) + "-" + str(uuid.uuid1())
        if verbose:
            print(f"Session id: {session_id}")

        # finally, invoke the supervisor request
        result = self.invoke(input_text=prompt, session_id=session_id, 
                             enable_trace=enable_trace,
                           trace_level=trace_level)
        return result

import inspect
from pydantic import create_model

def LocalTool(name, description):
    def decorator(func):
        # defining our model inheriting from pydantic.BaseModel and define fields as annotated attributes
        input_model = create_model(
            func.__name__ + "_input",
            **{
                name: (param.annotation, param.default)
                for name, param in inspect.signature(func).parameters.items()
                if param.default is not inspect.Parameter.empty
            },
        )

        # bedrock tool schema
        func.bedrock_schema = {
            'toolSpec': {
                'name': name,
                'description': description,
                'inputSchema': {
                    'json': input_model.schema()
                }
            }
        }
        return func

    return decorator