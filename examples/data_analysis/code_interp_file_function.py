## Be sure to have IAM permission to save and retrieve files from the agent file store
## folder in the bucket. Here is a sample policy:

# {
#     "Version": "2012-10-17",
#     "Statement": [
#         {
#             "Sid": "ListBucketWithPrefix",
#             "Effect": "Allow",
#             "Action": "s3:ListBucket",
#             "Resource": "arn:aws:s3:::*",
#             "Condition": {
#                 "StringLike": {
#                     "s3:prefix": [
#                         "AGENT_FILE_STORE/*",
#                           "CODE_INTERP_FILE_STORE/*"
#                     ]
#                 }
#             }
#         },
#         {
#             "Sid": "ReadWriteObjectsWithPrefix",
#             "Effect": "Allow",
#             "Action": [
#                 "s3:GetObject",
#                 "s3:PutObject"
#             ],
#             "Resource": "arn:aws:s3:::*/AGENT_FILE_STORE/*"
#         },
#         {
#             "Sid": "AmazonBedrockAgentInvokeSubAgentPolicy",
#             "Effect": "Allow",
#             "Action": "bedrock:InvokeAgent",
#             "Resource": [
#                   "arn:aws:bedrock:*:*:agent/ZNFUYDZIPL",
#                   "arn:aws:bedrock:*:*:agent-alias/ZNFUYDZIPL/*"
#         }
#     ]
# }

import json
import boto3
import pprint
from botocore.config import Config
import os

bedrock_agent_client = boto3.client('bedrock-agent')
bedrock_agent_runtime_client = boto3.client('bedrock-agent-runtime')
long_invoke_time_config = Config(read_timeout=600)

CODE_INTERP_AGENT_ID = 'ZNFUYDZIPL'
FILE_STORAGE_FOLDER = 'CODE_INTERP_FILE_STORE'

def get_named_parameter(event, name):
    return next(item for item in event['parameters'] if item['name'] == name)['value']
    
def populate_function_response(event, response_body):
    return {'response': {'actionGroup': event['actionGroup'], 'function': event['function'],
                'functionResponse': {'responseBody': {'TEXT': {'body': str(response_body)}}}}}

def cp_tmp_file_to_s3(bucket: str, file_name: str, tmp_file_path: str, session_id: str):
    print(f"Save to file called: {bucket}, {file_name}, from: {tmp_file_path}")

    # Get the contents of a file from the tmp_file_path
    with open(tmp_file_path, 'rb') as tmp_file:
        contents = tmp_file.read()

    # use boto3 to save contents to file in bucket
    s3 = boto3.resource('s3', config=long_invoke_time_config)
    response = s3.Object(bucket, f'{FILE_STORAGE_FOLDER}/{session_id}/{file_name}').put(Body=contents)
    print(response)
    return

def get_s3_file_content(bucket: str, file_name: str, session_id: str) -> str:
    print(f"Get file called: {file_name}, from bucket: {bucket}")
    # use boto3 to get file from bucket
    s3 = boto3.resource('s3', config=long_invoke_time_config)
    key = f"{FILE_STORAGE_FOLDER}/{session_id}/{file_name}"
    print(f"Retrieving {key} from s3 bucket {bucket}...")
    response = s3.Object(bucket, key).get()
    contents = response['Body'].read().decode('utf-8')

    return contents

# Return a session state populated with the files from the supplied list of filenames
def add_file_to_session_state(file_name, file_data, use_case='CODE_INTERPRETER', 
                            session_state=None):
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
                "data": file_data #open(file_name, "rb").read()
            }
        },
        "useCase": use_case
    }
    session_state['files'].append(named_file)
    return session_state

def invoke_code_interp_agent(query, input_files, input_file_bucket,
                             session_id, agent_id, alias_id='TSTALIASID', 
                             enable_trace=False,
                             session_state={}):

    end_session:bool = False
    
    if len(input_files) > 0:
        s3_files = []
        for input_file in input_files:
            s3_files.append({
                'bucket': input_file_bucket,
                'key': input_file
                })

        if enable_trace:
            print(f"Retrieving {len(s3_files)} files from agent file store for input to code interpreter...")

        for s3_file in s3_files:
            print(f"retrieving {s3_file['key']} from bucket: {input_file_bucket}, on session: {session_id}...")

            # tmp_file_path = "/tmp/customers.csv"
            # with open(tmp_file_path, 'w') as temp_file:
            #     temp_file.write('customer,total_sales_ytd\n')
            #     temp_file.write('ABC,100\n')
            #     temp_file.write('DEF,200\n')
            # cp_tmp_file_to_s3(s3_file['bucket'], s3_file['key'], tmp_file_path, session_id)

            # retrieve the file from s3 to /tmp
            content = get_s3_file_content(s3_file['bucket'], s3_file['key'], session_id)

            # add the retrieved content to the session as an input file to the code interpreter
            tmp_session_state = add_file_to_session_state(s3_file['key'], 
                                    content, 'CODE_INTERPRETER', 
                                    session_state)

    # invoke the agent API
    agentResponse = bedrock_agent_runtime_client.invoke_agent(
        inputText=query,
        agentId=agent_id,
        agentAliasId=alias_id, 
        sessionId=session_id,
        enableTrace=enable_trace, 
        endSession= end_session,
        sessionState=tmp_session_state
    )
    
    if enable_trace:
        print(pprint.pprint(agentResponse))
    
    event_stream = agentResponse['completion']
    try:
        for event in event_stream:        
            if 'chunk' in event:
                data = event['chunk']['bytes']
                if enable_trace:
                    print(f"Final answer ->\n{data.decode('utf8')}")
                agent_answer = data.decode('utf8')
                return agent_answer

            elif 'trace' in event:
                if enable_trace:
                    print(json.dumps(event['trace'], indent=2))
            else:
                raise Exception("unexpected event.", event)
                
    except Exception as e:
        raise Exception("unexpected event.", e)

def get_named_parameter(event, name):
    return next(item for item in event['parameters'] if item['name'] == name)['value']
    
def populate_function_response(event, response_body):
    return {'response': {'actionGroup': event['actionGroup'], 'function': event['function'],
                'functionResponse': {'responseBody': {'TEXT': {'body': str(response_body)}}}}}

def lambda_handler(event, context):
    print(event)
    
    function = event['function']
    session_id = event['sessionId']

    if function == "invoke_code_interp_agent":
        input_text = get_named_parameter(event, 'input_text')
        if not input_text:
            raise Exception("Missing mandatory parameter: input_text")

        input_file_list = get_named_parameter(event, 'input_file_list')
        if input_file_list is not None:
            input_files = input_file_list.split(',')
        else:
            input_files = []
        
        input_file_bucket = get_named_parameter(event, 'input_file_bucket')

        print(f"Invoking code interp agent...")
        result = invoke_code_interp_agent(input_text, input_files, input_file_bucket,
                                            session_id, CODE_INTERP_AGENT_ID,
                                            session_state = {},
                                            enable_trace=True)
    else:
        raise Exception(f"Unrecognized function: {function}")

    response = populate_function_response(event, result)
    print(response)
    return response
