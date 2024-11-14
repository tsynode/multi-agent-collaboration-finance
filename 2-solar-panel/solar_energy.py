import json
import random

def get_named_parameter(event, name):
    return next(item for item in event['parameters'] if item['name'] == name)['value']
    
def populate_function_response(event, response_body):
    return {'response': {'actionGroup': event['actionGroup'], 'function': event['function'],
                'functionResponse': {'responseBody': {'TEXT': {'body': str(response_body)}}}}}

def open_ticket(customer_id):
    # TODO: Implement real business logic
    random_int = random.randint(1, 9999)
    return "Thanks for contact customer {}! Your support case was generated with ID: {}".format(
        customer_id, random_int
    )

def lambda_handler(event, context):
    print(event)
    
    # name of the function that should be invoked
    function = event.get('function', '')

    # parameters to invoke function with
    parameters = event.get('parameters', [])
    
    if function == 'open_ticket':
        customer_id = get_named_parameter(event, "customer_id")
        result = open_ticket(customer_id)
    else:
        result = f"Error, function '{function}' not recognized"

    response = populate_function_response(event, result)
    print(response)
    return response
