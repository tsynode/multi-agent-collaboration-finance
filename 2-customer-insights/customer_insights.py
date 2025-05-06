import os
import json
import uuid
import boto3

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

def put_dynamodb(table_name, item):
    table = dynamodb_resource.Table(table_name)
    resp = table.put_item(Item=item)
    return resp

def read_dynamodb(
    table_name: str, 
    pk_field: str,
    pk_value: str,
    sk_field: str=None, 
    sk_value: str=None,
    attr_key: str=None,
    attr_val: str=None
):
    try:
        table = dynamodb_resource.Table(table_name)
        # Create expression
        if sk_field:
            key_expression = Key(pk_field).eq(pk_value) & Key(sk_field).eq(sk_value)
        else:
            key_expression = Key(pk_field).eq(pk_value)

        if attr_key:
            attr_expression = Attr(attr_key).eq(attr_val)
            query_data = table.query(
                KeyConditionExpression=key_expression,
                FilterExpression=attr_expression
            )
        else:
            query_data = table.query(
                KeyConditionExpression=key_expression
            )
        
        return query_data['Items']
    except Exception:
        print(f'Error querying table: {table_name}.')

def explain_visualization(data, visualization_type=None, customer_id=None, additional_context=None):
    """
    Main function to explain a financial visualization based on its underlying data
    
    Parameters:
    - data: The data that informed the visualization (JSON format)
    - visualization_type: Type of visualization (spending_trend, investment_allocation, etc.)
    - customer_id: Optional customer ID for personalized explanations
    - additional_context: Any additional context about the visualization
    
    Returns:
    - Natural language explanation of the visualization
    """
    # Parse the data if it's a string
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            return "Error: Unable to parse the visualization data. Please ensure it's valid JSON."
    
    # Determine visualization type if not explicitly provided
    if not visualization_type and 'visualization_type' in data:
        visualization_type = data['visualization_type']
    
    # Determine customer ID if not explicitly provided
    if not customer_id and 'customer_id' in data:
        customer_id = data['customer_id']
    
    # Call the appropriate explanation function based on visualization type
    if visualization_type == "spending_trend":
        return explain_spending_trend(data, customer_id, additional_context)
    elif visualization_type == "investment_allocation":
        return explain_investment_allocation(data, customer_id, additional_context)
    elif visualization_type == "cash_flow":
        return explain_cash_flow(data, customer_id, additional_context)
    elif visualization_type == "budget_performance":
        return explain_budget_performance(data, customer_id, additional_context)
    else:
        return f"I don't have an explanation model for {visualization_type} visualizations yet."

def explain_spending_trend(data, customer_id=None, additional_context=None):
    """Generate explanation for a spending trend visualization"""
    try:
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

def explain_investment_allocation(data, customer_id=None, additional_context=None):
    """Generate explanation for an investment allocation visualization"""
    try:
        # Extract key data points
        data_points = data.get('data_points', [])
        
        if not data_points:
            return "This investment allocation visualization doesn't contain any data points to analyze."
        
        # Calculate diversification metrics
        total_allocation = sum(point.get('percentage', 0) for point in data_points)
        largest_allocation = max(point.get('percentage', 0) for point in data_points)
        largest_asset = next((point.get('asset_class', 'Unknown') for point in data_points 
                             if point.get('percentage', 0) == largest_allocation), 'Unknown')
        
        # Determine risk profile
        stocks_percentage = next((point.get('percentage', 0) for point in data_points 
                                 if point.get('asset_class', '').lower() == 'stocks'), 0)
        bonds_percentage = next((point.get('percentage', 0) for point in data_points 
                                if point.get('asset_class', '').lower() == 'bonds'), 0)
        cash_percentage = next((point.get('percentage', 0) for point in data_points 
                               if point.get('asset_class', '').lower() == 'cash'), 0)
        
        if stocks_percentage > 70:
            risk_profile = "aggressive"
        elif stocks_percentage > 50:
            risk_profile = "moderate to aggressive"
        elif stocks_percentage > 30:
            risk_profile = "moderate"
        elif stocks_percentage > 15:
            risk_profile = "conservative to moderate"
        else:
            risk_profile = "conservative"
        
        # Generate explanation
        explanation = f"This investment allocation visualization for customer {customer_id} shows how their portfolio is distributed across different asset classes.\n\n"
        
        # Overall allocation
        explanation += f"The portfolio has a {risk_profile} risk profile, with the largest allocation ({largest_allocation}%) in {largest_asset}.\n\n"
        
        # Detailed breakdown
        explanation += "Asset allocation breakdown:\n"
        for point in data_points:
            asset_class = point.get('asset_class', 'Unknown')
            percentage = point.get('percentage', 0)
            explanation += f"- {asset_class}: {percentage}%\n"
        explanation += "\n"
        
        # Insights and recommendations
        explanation += "Key insights:\n"
        
        # Diversification assessment
        if largest_allocation > 60:
            explanation += f"- The portfolio is relatively concentrated, with {largest_allocation}% in {largest_asset}.\n"
            explanation += "- Consider diversifying to reduce risk exposure to a single asset class.\n"
        else:
            explanation += "- The portfolio shows good diversification across multiple asset classes.\n"
            explanation += "- Regular rebalancing will help maintain this diversification.\n"
        
        # Risk assessment
        if risk_profile == "aggressive":
            explanation += "- This is a high-risk portfolio suitable for long-term growth objectives.\n"
            explanation += "- Ensure this aligns with the customer's time horizon and risk tolerance.\n"
        elif risk_profile in ["moderate to aggressive", "moderate"]:
            explanation += "- This is a balanced portfolio with moderate risk.\n"
            explanation += "- Suitable for medium to long-term financial goals.\n"
        else:
            explanation += "- This is a conservative portfolio focused on capital preservation.\n"
            explanation += "- Consider whether this aligns with the customer's long-term growth needs.\n"
        
        return explanation
    
    except Exception as e:
        return f"Error analyzing investment allocation visualization: {str(e)}"

def explain_cash_flow(data, customer_id=None, additional_context=None):
    """Generate explanation for a cash flow visualization"""
    try:
        # Extract key data points
        data_points = data.get('data_points', [])
        time_period = data.get('time_period', '3_months')
        
        if not data_points:
            return "This cash flow visualization doesn't contain any data points to analyze."
        
        # Calculate key metrics
        total_income = sum(point.get('income', 0) for point in data_points)
        total_expenses = sum(point.get('expenses', 0) for point in data_points)
        net_cash_flow = total_income - total_expenses
        saving_rate = (net_cash_flow / total_income) * 100 if total_income > 0 else 0
        
        # Analyze monthly patterns
        monthly_savings = []
        for point in data_points:
            month = point.get('month', 'Unknown')
            income = point.get('income', 0)
            expenses = point.get('expenses', 0)
            savings = income - expenses
            saving_percentage = (savings / income) * 100 if income > 0 else 0
            monthly_savings.append((month, savings, saving_percentage))
        
        # Determine cash flow trend
        if len(monthly_savings) > 1:
            if monthly_savings[-1][1] > monthly_savings[0][1]:
                trend = "improving"
            elif monthly_savings[-1][1] < monthly_savings[0][1]:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "stable"
        
        # Generate explanation
        explanation = f"This cash flow visualization for customer {customer_id} shows their income and expenses over the past {time_period.replace('_', ' ')}.\n\n"
        
        # Overall cash flow
        if net_cash_flow > 0:
            explanation += f"Overall, the customer has a positive cash flow of ${net_cash_flow:,.2f}, "
            explanation += f"with a saving rate of {saving_rate:.1f}%.\n\n"
        else:
            explanation += f"Overall, the customer has a negative cash flow of ${abs(net_cash_flow):,.2f}, "
            explanation += "meaning they're spending more than they earn.\n\n"
        
        # Monthly breakdown
        explanation += "Monthly breakdown:\n"
        for month, savings, saving_percentage in monthly_savings:
            if savings >= 0:
                explanation += f"- {month}: Income ${point.get('income', 0):,.2f}, Expenses ${point.get('expenses', 0):,.2f}, "
                explanation += f"Savings ${savings:,.2f} ({saving_percentage:.1f}% of income)\n"
            else:
                explanation += f"- {month}: Income ${point.get('income', 0):,.2f}, Expenses ${point.get('expenses', 0):,.2f}, "
                explanation += f"Deficit ${abs(savings):,.2f}\n"
        explanation += "\n"
        
        # Insights and recommendations
        explanation += "Key insights:\n"
        
        # Cash flow assessment
        if net_cash_flow > 0 and saving_rate > 20:
            explanation += f"- Strong positive cash flow with an excellent saving rate of {saving_rate:.1f}%.\n"
            explanation += "- Consider allocating excess savings to investments or retirement accounts.\n"
        elif net_cash_flow > 0:
            explanation += f"- Positive cash flow with a saving rate of {saving_rate:.1f}%.\n"
            explanation += "- Consider strategies to increase the saving rate to 20% or higher.\n"
        else:
            explanation += "- Negative cash flow indicates spending exceeds income.\n"
            explanation += "- Recommend reviewing expenses to identify areas for potential reduction.\n"
        
        # Trend assessment
        if trend == "improving":
            explanation += "- Cash flow is improving month-over-month, indicating positive financial management.\n"
        elif trend == "declining":
            explanation += "- Cash flow is declining month-over-month, which may require attention.\n"
            explanation += "- Consider reviewing recent changes in income or spending patterns.\n"
        else:
            explanation += "- Cash flow is relatively stable month-over-month.\n"
        
        return explanation
    
    except Exception as e:
        return f"Error analyzing cash flow visualization: {str(e)}"

def explain_budget_performance(data, customer_id=None, additional_context=None):
    """Generate explanation for a budget performance visualization"""
    try:
        # Extract key data points
        data_points = data.get('data_points', [])
        
        if not data_points:
            return "This budget performance visualization doesn't contain any data points to analyze."
        
        # Calculate key metrics
        total_planned = sum(point.get('planned', 0) for point in data_points)
        total_actual = sum(point.get('actual', 0) for point in data_points)
        overall_variance = total_actual - total_planned
        variance_percentage = (overall_variance / total_planned) * 100 if total_planned > 0 else 0
        
        # Analyze category variances
        category_variances = []
        for point in data_points:
            category = point.get('category', 'Unknown')
            planned = point.get('planned', 0)
            actual = point.get('actual', 0)
            variance = actual - planned
            variance_pct = (variance / planned) * 100 if planned > 0 else 0
            category_variances.append((category, planned, actual, variance, variance_pct))
        
        # Sort categories by absolute variance percentage
        category_variances.sort(key=lambda x: abs(x[4]), reverse=True)
        
        # Generate explanation
        explanation = f"This budget performance visualization for customer {customer_id} compares planned versus actual spending across different categories.\n\n"
        
        # Overall budget performance
        if variance_percentage > 0:
            explanation += f"Overall, spending was ${total_actual:,.2f}, which is ${overall_variance:,.2f} "
            explanation += f"({variance_percentage:.1f}%) over the planned budget of ${total_planned:,.2f}.\n\n"
        elif variance_percentage < 0:
            explanation += f"Overall, spending was ${total_actual:,.2f}, which is ${abs(overall_variance):,.2f} "
            explanation += f"({abs(variance_percentage):.1f}%) under the planned budget of ${total_planned:,.2f}.\n\n"
        else:
            explanation += f"Overall, spending exactly matched the planned budget of ${total_planned:,.2f}.\n\n"
        
        # Categories with significant variances
        explanation += "Categories with significant variances:\n"
        significant_variances = [v for v in category_variances if abs(v[4]) > 10]  # >10% variance
        
        if significant_variances:
            for category, planned, actual, variance, variance_pct in significant_variances:
                if variance_pct > 0:
                    explanation += f"- {category}: ${actual:,.2f} spent vs. ${planned:,.2f} planned "
                    explanation += f"(${variance:,.2f} or {variance_pct:.1f}% over budget)\n"
                else:
                    explanation += f"- {category}: ${actual:,.2f} spent vs. ${planned:,.2f} planned "
                    explanation += f"(${abs(variance):,.2f} or {abs(variance_pct):.1f}% under budget)\n"
        else:
            explanation += "- No categories showed significant variance from the budget.\n"
        explanation += "\n"
        
        # Insights and recommendations
        explanation += "Key insights:\n"
        
        # Overall budget assessment
        if variance_percentage > 10:
            explanation += f"- Overall spending is significantly over budget ({variance_percentage:.1f}%).\n"
            explanation += "- Consider reviewing and adjusting the budget or spending habits.\n"
        elif variance_percentage < -10:
            explanation += f"- Overall spending is significantly under budget ({abs(variance_percentage):.1f}%).\n"
            explanation += "- The budget may be too conservative or there might be delayed expenses.\n"
        else:
            explanation += "- Overall budget adherence is good, with only minor variances.\n"
            explanation += "- Continue monitoring to maintain this performance.\n"
        
        # Category-specific insights
        if significant_variances:
            over_budget = [v for v in significant_variances if v[4] > 0]
            if over_budget:
                worst_category = over_budget[0]
                explanation += f"- The {worst_category[0]} category shows the largest over-budget spending "
                explanation += f"({worst_category[4]:.1f}%).\n"
                explanation += "- Consider strategies to better control spending in this area.\n"
            
            under_budget = [v for v in significant_variances if v[4] < 0]
            if under_budget:
                most_under = under_budget[0]
                explanation += f"- The {most_under[0]} category is significantly under budget "
                explanation += f"({abs(most_under[4]):.1f}%).\n"
                explanation += "- Consider whether this represents savings or delayed expenses.\n"
        
        return explanation
    
    except Exception as e:
        return f"Error analyzing budget performance visualization: {str(e)}"

def recommend_financial_products(visualization_type, data, customer_id=None):
    """Recommend financial products based on visualization insights"""
    try:
        # Parse the data if it's a string
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                return "Error: Unable to parse the visualization data. Please ensure it's valid JSON."
        
        # Determine customer ID if not explicitly provided
        if not customer_id and 'customer_id' in data:
            customer_id = data['customer_id']
        
        recommendations = []
        
        if visualization_type == "spending_trend":
            # Extract key data points
            data_points = data.get('data_points', [])
            if not data_points:
                return "Unable to recommend products without spending trend data."
            
            # Calculate key metrics
            amounts = [point.get('amount', 0) for point in data_points]
            average_spending = sum(amounts) / len(amounts) if amounts else 0
            
            # Trend analysis
            if len(amounts) > 1:
                if amounts[-1] > amounts[0] * 1.1:  # 10% increase
                    recommendations.append("Budgeting App: To help track and manage increasing expenses")
                    recommendations.append("High-Yield Savings Account: To build an emergency fund as expenses increase")
                elif amounts[-1] < amounts[0] * 0.9:  # 10% decrease
                    recommendations.append("Investment Account: To put saved money to work")
                    recommendations.append("Retirement Contribution Increase: Good time to boost retirement savings")
            
            # Volatility analysis
            spending_volatility = sum(abs(amt - average_spending) for amt in amounts) / len(amounts) / average_spending if average_spending else 0
            if spending_volatility > 0.2:  # High volatility
                recommendations.append("Flexible Credit Line: For managing cash flow during spending fluctuations")
                recommendations.append("Emergency Fund: To cover unexpected expenses")
        
        elif visualization_type == "investment_allocation":
            # Extract key data points
            data_points = data.get('data_points', [])
            if not data_points:
                return "Unable to recommend products without investment allocation data."
            
            # Calculate diversification metrics
            stocks_percentage = next((point.get('percentage', 0) for point in data_points 
                                     if point.get('asset_class', '').lower() == 'stocks'), 0)
            bonds_percentage = next((point.get('percentage', 0) for point in data_points 
                                    if point.get('asset_class', '').lower() == 'bonds'), 0)
            cash_percentage = next((point.get('percentage', 0) for point in data_points 
                                   if point.get('asset_class', '').lower() == 'cash'), 0)
            
            if stocks_percentage > 70:
                recommendations.append("Bond ETFs: To balance the high stock allocation")
                recommendations.append("Downside Protection Products: To hedge against market volatility")
            elif stocks_percentage < 30:
                recommendations.append("Growth-Oriented ETFs: To increase potential returns")
                recommendations.append("Dividend Stocks: To generate income while adding growth potential")
            
            if cash_percentage > 20:
                recommendations.append("Short-Term Bond Funds: Better returns than cash with low risk")
                recommendations.append("CD Ladder: To maximize yield on cash holdings")
        
        elif visualization_type == "cash_flow":
            # Extract key data points
            data_points = data.get('data_points', [])
            if not data_points:
                return "Unable to recommend products without cash flow data."
            
            # Calculate key metrics
            total_income = sum(point.get('income', 0) for point in data_points)
            total_expenses = sum(point.get('expenses', 0) for point in data_points)
            net_cash_flow = total_income - total_expenses
            
            if net_cash_flow > 0:
                saving_rate = (net_cash_flow / total_income) * 100 if total_income > 0 else 0
                if saving_rate > 20:
                    recommendations.append("Investment Account: To put excess cash flow to work")
                    recommendations.append("Tax-Advantaged Retirement Accounts: To maximize tax benefits")
                else:
                    recommendations.append("Automatic Savings Plan: To increase saving rate")
                    recommendations.append("High-Yield Savings Account: For emergency fund building")
            else:
                recommendations.append("Debt Consolidation: To reduce interest expenses")
                recommendations.append("Budgeting Tools: To help identify areas for expense reduction")
                recommendations.append("Balance Transfer Credit Card: To manage high-interest debt")
        
        elif visualization_type == "budget_performance":
            # Extract key data points
            data_points = data.get('data_points', [])
            if not data_points:
                return "Unable to recommend products without budget performance data."
            
            # Calculate key metrics
            total_planned = sum(point.get('planned', 0) for point in data_points)
            total_actual = sum(point.get('actual', 0) for point in data_points)
            overall_variance = total_actual - total_planned
            variance_percentage = (overall_variance / total_planned) * 100 if total_planned > 0 else 0
            
            if variance_percentage > 10:
                recommendations.append("Expense Tracking App: To help identify and control overspending")
                recommendations.append("Automated Savings: To ensure saving happens before spending")
            elif variance_percentage < -10:
                recommendations.append("Goal-Based Savings Accounts: To allocate unspent funds to specific goals")
                recommendations.append("Investment Account: To put excess savings to work")
            else:
                recommendations.append("Rewards Credit Card: To maximize benefits on planned spending")
                recommendations.append("Financial Planning Services: To build on successful budget management")
        
        # Format recommendations
        if recommendations:
            result = f"Based on the {visualization_type.replace('_', ' ')} visualization for customer {customer_id}, here are some recommended financial products:\n\n"
            for i, rec in enumerate(recommendations, 1):
                product, reason = rec.split(": ", 1)
                result += f"{i}. **{product}** - {reason}\n"
            return result
        else:
            return f"No specific product recommendations based on the {visualization_type.replace('_', ' ')} visualization."
    
    except Exception as e:
        return f"Error generating product recommendations: {str(e)}"

def create_support_ticket(customer_id, description):
    """Create a support ticket for visualization explanation assistance"""
    ticket_id = str(uuid.uuid1())
    item = {
        'ticket_id': ticket_id,
        'customer_id': customer_id,
        'description': description,
        'status': 'created',
        'type': 'visualization_explanation'
    }
    resp = put_dynamodb(dynamodb_table, item)
    print(resp)
    return f"Support ticket created for customer {customer_id}. A financial advisor will review the visualization and provide a detailed explanation. Ticket ID: {ticket_id}"

def get_support_tickets(customer_id, ticket_id=None):
    """Get support tickets for a customer"""
    return read_dynamodb(dynamodb_table, 
                         dynamodb_pk,
                         customer_id,
                         dynamodb_sk,
                         ticket_id)

def lambda_handler(event, context):
    print(event)
    
    # name of the function that should be invoked
    function = event.get('function', '')

    # parameters to invoke function with
    parameters = event.get('parameters', [])
    customer_id = get_named_parameter(event, "customer_id")

    if function == 'explain_visualization':
        visualization_type = get_named_parameter(event, "visualization_type")
        data = get_named_parameter(event, "data")
        additional_context = get_named_parameter(event, "additional_context")
        result = explain_visualization(data, visualization_type, customer_id, additional_context)
    elif function == 'explain_spending_trend':
        data = get_named_parameter(event, "data")
        additional_context = get_named_parameter(event, "additional_context")
        result = explain_spending_trend(data, customer_id, additional_context)
    elif function == 'explain_investment_allocation':
        data = get_named_parameter(event, "data")
        additional_context = get_named_parameter(event, "additional_context")
        result = explain_investment_allocation(data, customer_id, additional_context)
    elif function == 'explain_cash_flow':
        data = get_named_parameter(event, "data")
        additional_context = get_named_parameter(event, "additional_context")
        result = explain_cash_flow(data, customer_id, additional_context)
    elif function == 'explain_budget_performance':
        data = get_named_parameter(event, "data")
        additional_context = get_named_parameter(event, "additional_context")
        result = explain_budget_performance(data, customer_id, additional_context)
    elif function == 'recommend_financial_products':
        visualization_type = get_named_parameter(event, "visualization_type")
        data = get_named_parameter(event, "data")
        result = recommend_financial_products(visualization_type, data, customer_id)
    elif function == 'create_support_ticket':
        description = get_named_parameter(event, "description")
        result = create_support_ticket(customer_id, description)
    elif function == 'get_support_tickets':
        ticket_id = get_named_parameter(event, "ticket_id")
        result = get_support_tickets(customer_id, ticket_id)
    else:
        result = f"Error, function '{function}' not recognized"

    response = populate_function_response(event, result)
    print(response)
    return response
