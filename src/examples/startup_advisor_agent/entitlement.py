import sys

import boto3
import requests
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest


def sign_request(req, service, region):
    session = boto3.Session()
    credentials = session.get_credentials().get_frozen_credentials()

    # Convert requests.PreparedRequest to AWSRequest
    aws_req = AWSRequest(
        method=req.method, url=req.url, data=req.body, headers=req.headers
    )

    # Sign the AWSRequest with SigV4Auth
    SigV4Auth(credentials, service, region).add_auth(aws_req)

    # Update the original requests.PreparedRequest with the signed headers
    req.headers.update(aws_req.headers)

    return req


# Create a request using the requests library and command line arguments
# > python3 script.py STAGE REGION MODEL_ID
if len(sys.argv) != 4:
    sys.exit("Invalid arguments. Usage: entitlement.py STAGE REGION MODEL_ID")
stage = sys.argv[1]
if not stage in ["beta", "preprod", "prod"]:
    sys.exit("Invalid stage. Must be one of: [beta, preprod, prod]")
region = sys.argv[2]
service = "bedrock"
url = f"https://bedrock.{region}.amazonaws.com/foundation-model-entitlement"
if stage != "prod":
    url = f"https://{stage}.{region}.controlplane.bedrock.aws.dev/foundation-model-entitlement"
model_id = sys.argv[3]

req = requests.Request("POST", url, json={"modelId": model_id})
prepared_req = req.prepare()

# Sign the request
sign_request(prepared_req, service, region)

# Send the request
session = requests.Session()
response = session.send(prepared_req)

print(
    f"Attaining Foundation Model Entitlement Status: {response.status_code}, Response: {response.json()}"
)
