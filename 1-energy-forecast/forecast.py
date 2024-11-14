import json

def get_named_parameter(event, name):
    return next(item for item in event['parameters'] if item['name'] == name)['value']
    
def populate_function_response(event, response_body):
    return {'response': {'actionGroup': event['actionGroup'], 'function': event['function'],
                'functionResponse': {'responseBody': {'TEXT': {'body': str(response_body)}}}}}

def forecast_consumption(customer_id):
    # TODO: Implement real business logic
    return [
        {"day": "2024/06/01",
         "sumPowerReading": "120.0"
        },
        {"day": "2024/07/01",
         "sumPowerReading": "130.0"
        },
        {"day": "2024/08/01",
         "sumPowerReading": "140.0"
        },
        {"day": "2024/09/01",
         "sumPowerReading": "150.0"
        },
        {"day": "2024/10/01",
         "sumPowerReading": "200.0"
        },
        {"day": "2024/11/01",
         "sumPowerReading": "190.0"
        },
        {"day": "2024/12/01",
         "sumPowerReading": "205.0"
        },
        {"day": "2025/01/01",
         "sumPowerReading": "210.0"
        }
    ]

def lambda_handler(event, context):
    print(event)
    
    # name of the function that should be invoked
    function = event.get('function', '')

    # parameters to invoke function with
    parameters = event.get('parameters', [])
    
    if function == 'forecast_consumption':
        customer_id = get_named_parameter(event, "customer_id")
        result = forecast_consumption(customer_id)
    else:
        result = f"Error, function '{function}' not recognized"

    response = populate_function_response(event, result)
    print(response)
    return response
