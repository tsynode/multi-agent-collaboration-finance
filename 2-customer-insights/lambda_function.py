import boto3
import json
import os

from boto3.dynamodb.conditions import Key, Attr
from datetime import datetime
from decimal import Decimal

dynamodb_resource = boto3.resource('dynamodb')
dynamodb_table = os.getenv('dynamodb_table')
dynamodb_pk = os.getenv('dynamodb_pk')
dynamodb_sk = os.getenv('dynamodb_sk')


def get_named_parameter(event, name):
    try:
        return next(item for item in event['parameters'] if item['name'] == name)['value']
    except:
        return None
    
def populate_function_response(event, response_body):
    return {'response': {'actionGroup': event['actionGroup'], 'function': event['function'],
                'functionResponse': {'responseBody': {'TEXT': {'body': str(response_body)}}}}}


def explain_spending_trend(data, customer_id=None, additional_context=None):
    """Generate explanation for a spending trend visualization"""
    try:
        # Parse data if it's a string
        if isinstance(data, str):
            data = json.loads(data)
            
        # Extract key data points
        data_points = data.get('data_points', [])
        categories = data.get('categories', [])
        time_period = data.get('time_period', '6_months')
        
        if not data_points:
            return "This spending trend visualization doesn't contain any data points to analyze."
        
        # Calculate key metrics
        amounts = [point.get('amount', 0) for point in data_points]
        total_spending = sum(amounts)
        average_spending = total_spending / len(amounts) if amounts else 0
        min_spending = min(amounts) if amounts else 0
        max_spending = max(amounts) if amounts else 0
        
        # Find trends
        trend_direction = "stable"
        if len(amounts) > 1:
            if amounts[-1] > amounts[0] * 1.1:  # 10% increase
                trend_direction = "increasing"
            elif amounts[-1] < amounts[0] * 0.9:  # 10% decrease
                trend_direction = "decreasing"
        
        # Find anomalies (values that deviate significantly from the average)
        anomalies = []
        for i, amount in enumerate(amounts):
            if amount > average_spending * 1.3:  # 30% above average
                anomalies.append((i, "significantly higher"))
            elif amount < average_spending * 0.7:  # 30% below average
                anomalies.append((i, "significantly lower"))
        
        # Generate explanation
        explanation = f"This spending trend visualization for customer {customer_id} shows their spending patterns over the past {time_period.replace('_', ' ')}.\n\n"
        
        # Overall trend
        explanation += f"Overall, the customer's spending is {trend_direction}. "
        explanation += f"They spent a total of ${total_spending:,.2f}, with an average monthly spending of ${average_spending:,.2f}. "
        explanation += f"Their spending ranged from ${min_spending:,.2f} to ${max_spending:,.2f}.\n\n"
        
        # Anomalies
        if anomalies:
            explanation += "Notable spending patterns:\n"
            for idx, description in anomalies:
                month = data_points[idx].get('month', f"period {idx+1}")
                explanation += f"- {month}: ${amounts[idx]:,.2f} ({description} than average)\n"
            explanation += "\n"
        
        # Category breakdown if available
        if categories:
            explanation += "Spending by category:\n"
            for category in categories:
                name = category.get('name', 'Unknown')
                percentage = category.get('percentage', 0)
                explanation += f"- {name}: {percentage}% of total spending\n"
            explanation += "\n"
        
        # Insights and recommendations
        explanation += "Key insights:\n"
        if trend_direction == "increasing":
            explanation += "- Spending has been increasing, which may indicate changing financial needs or lifestyle.\n"
            explanation += "- Consider reviewing the budget to ensure spending aligns with financial goals.\n"
        elif trend_direction == "decreasing":
            explanation += "- Spending has been decreasing, which could indicate improved budget management.\n"
            explanation += "- Consider allocating the saved funds to savings or investments.\n"
        else:
            explanation += "- Spending has remained relatively stable, indicating consistent financial habits.\n"
            explanation += "- Regular budget reviews can help maintain this stability.\n"
        
        return explanation
    
    except Exception as e:
        return f"Error analyzing spending trend visualization: {str(e)}"


def lambda_handler(event, context):
    print(event)
    
    # name of the function that should be invoked
    function = event.get('function', '')

    # parameters to invoke function with
    parameters = event.get('parameters', [])
    customer_id = get_named_parameter(event, "customer_id")

    # Call the appropriate function based on the function name
    if function == 'explain_spending_trend':
        data = get_named_parameter(event, "data")
        additional_context = get_named_parameter(event, "additional_context")
        result = explain_spending_trend(data, customer_id, additional_context)
    else:
        # Default response for functions not yet implemented
        result = f"Function '{function}' not yet implemented in this version."

    response = populate_function_response(event, result)
    print(response)
    return response
