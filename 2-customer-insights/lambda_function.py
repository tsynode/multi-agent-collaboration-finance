import boto3
import json
import os
import uuid

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
            return "Unable to explain the spending trend visualization without data points."
        
        # Calculate key metrics
        amounts = [point.get('amount', 0) for point in data_points]
        months = [point.get('month', '') for point in data_points]
        
        total_spending = sum(amounts)
        avg_monthly_spending = total_spending / len(amounts) if amounts else 0
        max_spending = max(amounts) if amounts else 0
        max_spending_month = months[amounts.index(max_spending)] if amounts and max_spending > 0 else "N/A"
        min_spending = min(amounts) if amounts else 0
        min_spending_month = months[amounts.index(min_spending)] if amounts and min_spending > 0 else "N/A"
        
        # Calculate trend
        if len(amounts) > 1:
            first_month = amounts[0]
            last_month = amounts[-1]
            trend_percentage = ((last_month - first_month) / first_month) * 100 if first_month > 0 else 0
            trend_direction = "increased" if trend_percentage > 0 else "decreased" if trend_percentage < 0 else "remained stable"
        else:
            trend_percentage = 0
            trend_direction = "cannot be determined (insufficient data)"
        
        # Generate category insights
        category_insights = ""
        if categories:
            top_categories = sorted(categories, key=lambda x: x.get('percentage', 0), reverse=True)
            top_category = top_categories[0]
            category_insights = f"\n\nThe largest spending category is {top_category.get('name', 'Unknown')} at {top_category.get('percentage', 0)}% of total spending."
            
            if len(top_categories) > 1:
                second_category = top_categories[1]
                category_insights += f" This is followed by {second_category.get('name', 'Unknown')} at {second_category.get('percentage', 0)}%."
        
        # Generate personalized insights based on customer ID
        personalized_insights = ""
        if customer_id:
            personalized_insights = f"\n\nBased on your historical spending patterns, your {time_period.replace('_', ' ')} spending is "
            if trend_percentage > 10:
                personalized_insights += "significantly higher than usual. Consider reviewing your budget to identify areas where you might cut back."
            elif trend_percentage < -10:
                personalized_insights += "lower than usual. Great job managing your expenses!"
            else:
                personalized_insights += "in line with your typical patterns."
        
        # Construct the explanation
        explanation = f"This visualization shows your spending trend over the past {time_period.replace('_', ' ')}.\n\n"
        explanation += f"Your total spending during this period was ${total_spending:,.2f}, with an average monthly spending of ${avg_monthly_spending:,.2f}.\n\n"
        explanation += f"Your highest spending month was {max_spending_month} (${max_spending:,.2f}), and your lowest was {min_spending_month} (${min_spending:,.2f}).\n\n"
        explanation += f"Over this period, your spending has {trend_direction} by {abs(trend_percentage):.1f}%."
        explanation += category_insights
        explanation += personalized_insights
        
        # Add context-specific insights if provided
        if additional_context:
            explanation += f"\n\nAdditional context: {additional_context}"
        
        return explanation
    
    except Exception as e:
        return f"Error generating spending trend explanation: {str(e)}"

def explain_investment_allocation(data, customer_id=None, additional_context=None):
    """Generate explanation for an investment allocation visualization"""
    try:
        # Extract key data points
        allocations = data.get('allocations', [])
        risk_profile = data.get('risk_profile', 'moderate')
        time_horizon = data.get('time_horizon', 'medium_term')
        
        if not allocations:
            return "Unable to explain the investment allocation visualization without allocation data."
        
        # Calculate key metrics
        total_investment = sum(allocation.get('amount', 0) for allocation in allocations)
        allocation_percentages = {allocation.get('asset_class', 'Unknown'): (allocation.get('amount', 0) / total_investment) * 100 if total_investment > 0 else 0 for allocation in allocations}
        
        # Determine asset class distribution
        stocks_percentage = allocation_percentages.get('Stocks', 0)
        bonds_percentage = allocation_percentages.get('Bonds', 0)
        cash_percentage = allocation_percentages.get('Cash', 0)
        alternative_percentage = allocation_percentages.get('Alternative Investments', 0)
        
        # Analyze risk profile
        risk_assessment = ""
        if stocks_percentage > 70:
            risk_assessment = "aggressive"
        elif stocks_percentage > 50:
            risk_assessment = "moderately aggressive"
        elif stocks_percentage > 30:
            risk_assessment = "moderate"
        else:
            risk_assessment = "conservative"
        
        # Generate personalized insights based on customer ID and risk profile
        personalized_insights = ""
        if customer_id:
            if risk_profile == 'aggressive' and risk_assessment == 'conservative':
                personalized_insights = "\n\nYour current allocation is more conservative than your stated risk tolerance. Consider increasing your exposure to growth assets if appropriate for your goals."
            elif risk_profile == 'conservative' and risk_assessment == 'aggressive':
                personalized_insights = "\n\nYour current allocation is more aggressive than your stated risk tolerance. Consider reducing your exposure to volatile assets to better align with your comfort level."
            elif time_horizon == 'short_term' and stocks_percentage > 50:
                personalized_insights = "\n\nGiven your short-term investment horizon, your allocation to stocks may be higher than typically recommended. Consider increasing your allocation to more stable assets."
            elif time_horizon == 'long_term' and stocks_percentage < 50:
                personalized_insights = "\n\nGiven your long-term investment horizon, you might consider increasing your allocation to growth assets to potentially enhance long-term returns."
        
        # Construct the explanation
        explanation = f"This visualization shows your current investment allocation across different asset classes.\n\n"
        explanation += f"Your total investment portfolio is valued at ${total_investment:,.2f}, distributed as follows:\n\n"
        
        for asset_class, percentage in allocation_percentages.items():
            explanation += f"- {asset_class}: {percentage:.1f}%\n"
        
        explanation += f"\nBased on this allocation, your portfolio has a {risk_assessment} risk profile."
        
        if time_horizon:
            explanation += f" This is aligned with your {time_horizon.replace('_', ' ')} investment horizon."
        
        explanation += personalized_insights
        
        # Add context-specific insights if provided
        if additional_context:
            explanation += f"\n\nAdditional context: {additional_context}"
        
        return explanation
    
    except Exception as e:
        return f"Error generating investment allocation explanation: {str(e)}"

def explain_cash_flow(data, customer_id=None, additional_context=None):
    """Generate explanation for a cash flow visualization"""
    try:
        # Extract key data points
        income_streams = data.get('income_streams', [])
        expenses = data.get('expenses', [])
        time_period = data.get('time_period', 'monthly')
        
        if not income_streams and not expenses:
            return "Unable to explain the cash flow visualization without income or expense data."
        
        # Calculate key metrics
        total_income = sum(stream.get('amount', 0) for stream in income_streams)
        total_expenses = sum(expense.get('amount', 0) for expense in expenses)
        net_cash_flow = total_income - total_expenses
        savings_rate = (net_cash_flow / total_income) * 100 if total_income > 0 else 0
        
        # Categorize expenses
        expense_categories = {}
        for expense in expenses:
            category = expense.get('category', 'Other')
            amount = expense.get('amount', 0)
            if category in expense_categories:
                expense_categories[category] += amount
            else:
                expense_categories[category] = amount
        
        # Find top expense categories
        top_expenses = sorted(expense_categories.items(), key=lambda x: x[1], reverse=True)
        
        # Analyze cash flow health
        if net_cash_flow > 0:
            cash_flow_health = "positive"
            cash_flow_advice = "You're living within your means and building savings."
        elif net_cash_flow == 0:
            cash_flow_health = "balanced"
            cash_flow_advice = "You're living within your means but not building savings."
        else:
            cash_flow_health = "negative"
            cash_flow_advice = "You're spending more than you earn, which is not sustainable long-term."
        
        # Generate personalized insights based on customer ID
        personalized_insights = ""
        if customer_id:
            if net_cash_flow < 0:
                personalized_insights = f"\n\nBased on your current spending patterns, you might consider reducing expenses in your top spending category: {top_expenses[0][0]} (${top_expenses[0][1]:,.2f} per {time_period})."
            elif savings_rate < 10:
                personalized_insights = f"\n\nWhile your cash flow is positive, your savings rate of {savings_rate:.1f}% is below the recommended 15-20%. Consider ways to increase your income or reduce expenses to boost your savings rate."
            elif savings_rate > 30:
                personalized_insights = f"\n\nYour savings rate of {savings_rate:.1f}% is excellent! You might consider investing some of your surplus to potentially grow your wealth further."
        
        # Construct the explanation
        explanation = f"This visualization shows your {time_period} cash flow, comparing income and expenses.\n\n"
        explanation += f"Your total {time_period} income is ${total_income:,.2f}, while your total expenses are ${total_expenses:,.2f}.\n\n"
        explanation += f"This results in a {cash_flow_health} net cash flow of ${net_cash_flow:,.2f} and a savings rate of {savings_rate:.1f}%. {cash_flow_advice}\n\n"
        
        if top_expenses:
            explanation += "Your top expense categories are:\n\n"
            for i, (category, amount) in enumerate(top_expenses[:3], 1):
                percentage = (amount / total_expenses) * 100 if total_expenses > 0 else 0
                explanation += f"{i}. {category}: ${amount:,.2f} ({percentage:.1f}% of total expenses)\n"
        
        explanation += personalized_insights
        
        # Add context-specific insights if provided
        if additional_context:
            explanation += f"\n\nAdditional context: {additional_context}"
        
        return explanation
    
    except Exception as e:
        return f"Error generating cash flow explanation: {str(e)}"

def explain_budget_performance(data, customer_id=None, additional_context=None):
    """Generate explanation for a budget performance visualization"""
    try:
        # Extract key data points
        data_points = data.get('data_points', [])
        time_period = data.get('time_period', 'monthly')
        
        if not data_points:
            return "Unable to explain the budget performance visualization without data points."
        
        # Calculate key metrics
        total_planned = sum(point.get('planned', 0) for point in data_points)
        total_actual = sum(point.get('actual', 0) for point in data_points)
        overall_variance = total_actual - total_planned
        variance_percentage = (overall_variance / total_planned) * 100 if total_planned > 0 else 0
        
        # Analyze variances by category
        categories_over_budget = []
        categories_under_budget = []
        
        for point in data_points:
            category = point.get('category', 'Unknown')
            planned = point.get('planned', 0)
            actual = point.get('actual', 0)
            variance = actual - planned
            variance_pct = (variance / planned) * 100 if planned > 0 else 0
            
            if variance > 0 and variance_pct > 5:
                categories_over_budget.append((category, variance, variance_pct))
            elif variance < 0 and abs(variance_pct) > 5:
                categories_under_budget.append((category, variance, variance_pct))
        
        # Sort categories by variance percentage
        categories_over_budget.sort(key=lambda x: x[2], reverse=True)
        categories_under_budget.sort(key=lambda x: abs(x[2]), reverse=True)
        
        # Determine overall budget status
        if variance_percentage > 5:
            budget_status = "over budget"
            status_color = "red"
        elif variance_percentage < -5:
            budget_status = "under budget"
            status_color = "green"
        else:
            budget_status = "on target"
            status_color = "blue"
        
        # Generate personalized insights based on customer ID
        personalized_insights = ""
        if customer_id:
            if categories_over_budget:
                top_over = categories_over_budget[0]
                personalized_insights = f"\n\nYour largest budget variance is in the {top_over[0]} category, where you spent ${top_over[1]:,.2f} ({top_over[2]:.1f}%) more than planned."
                
                if len(categories_over_budget) > 1:
                    second_over = categories_over_budget[1]
                    personalized_insights += f" Your second largest variance is in {second_over[0]} at ${second_over[1]:,.2f} ({second_over[2]:.1f}%) over budget."
            
            if budget_status == "over budget":
                personalized_insights += "\n\nConsider reviewing your spending in these categories to identify opportunities to reduce expenses and stay within your budget."
        
        # Construct the explanation
        explanation = f"This visualization shows your {time_period} budget performance, comparing planned versus actual spending.\n\n"
        explanation += f"Your total planned spending was ${total_planned:,.2f}, while your actual spending was ${total_actual:,.2f}.\n\n"
        explanation += f"Overall, you are {budget_status} by ${abs(overall_variance):,.2f} ({abs(variance_percentage):.1f}%).\n\n"
        
        if categories_over_budget:
            explanation += "Categories where you spent more than budgeted:\n\n"
            for category, variance, variance_pct in categories_over_budget[:3]:
                explanation += f"- {category}: ${variance:,.2f} ({variance_pct:.1f}%) over budget\n"
            explanation += "\n"
        
        if categories_under_budget:
            explanation += "Categories where you spent less than budgeted:\n\n"
            for category, variance, variance_pct in categories_under_budget[:3]:
                explanation += f"- {category}: ${abs(variance):,.2f} ({abs(variance_pct):.1f}%) under budget\n"
        
        explanation += personalized_insights
        
        # Add context-specific insights if provided
        if additional_context:
            explanation += f"\n\nAdditional context: {additional_context}"
        
        return explanation
    
    except Exception as e:
        return f"Error generating budget performance explanation: {str(e)}"

def recommend_financial_products(visualization_type, data, customer_id=None):
    """Recommend financial products based on visualization insights"""
    try:
        # Parse the data if it's a string
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                return "Error: Unable to parse the visualization data. Please ensure it's valid JSON."
        
        recommendations = []
        
        # Tailor recommendations based on visualization type
        if visualization_type == "spending_trend":
            # Extract key data points
            data_points = data.get('data_points', [])
            categories = data.get('categories', [])
            
            if not data_points:
                return "Unable to recommend products without spending trend data."
            
            # Calculate trend
            amounts = [point.get('amount', 0) for point in data_points]
            if len(amounts) > 1:
                first_month = amounts[0]
                last_month = amounts[-1]
                trend_percentage = ((last_month - first_month) / first_month) * 100 if first_month > 0 else 0
            else:
                trend_percentage = 0
            
            # Find top spending categories
            top_categories = []
            if categories:
                top_categories = sorted(categories, key=lambda x: x.get('percentage', 0), reverse=True)
            
            # Make recommendations based on spending patterns
            if trend_percentage > 10:
                recommendations.append("Budgeting App: To help track and control increasing expenses")
                recommendations.append("High-Yield Savings Account: To build an emergency fund for unexpected expenses")
            elif trend_percentage < -10:
                recommendations.append("Investment Account: To put your saved money to work")
                recommendations.append("Rewards Credit Card: To maximize benefits on your controlled spending")
            
            if top_categories and top_categories[0].get('name') == 'Dining':
                recommendations.append("Dining Rewards Credit Card: To earn cashback on your frequent restaurant spending")
            elif top_categories and top_categories[0].get('name') == 'Travel':
                recommendations.append("Travel Rewards Credit Card: To earn points on your frequent travel spending")
        
        elif visualization_type == "investment_allocation":
            # Extract key data points
            allocations = data.get('allocations', [])
            risk_profile = data.get('risk_profile', 'moderate')
            time_horizon = data.get('time_horizon', 'medium_term')
            
            if not allocations:
                return "Unable to recommend products without investment allocation data."
            
            # Calculate asset class distribution
            total_investment = sum(allocation.get('amount', 0) for allocation in allocations)
            allocation_percentages = {allocation.get('asset_class', 'Unknown'): (allocation.get('amount', 0) / total_investment) * 100 if total_investment > 0 else 0 for allocation in allocations}
            
            stocks_percentage = allocation_percentages.get('Stocks', 0)
            bonds_percentage = allocation_percentages.get('Bonds', 0)
            
            # Make recommendations based on allocation
            if risk_profile == 'aggressive' and stocks_percentage < 60:
                recommendations.append("Growth ETF Portfolio: To increase your exposure to growth assets")
                recommendations.append("Sector-Specific Funds: To target high-growth industries")
            elif risk_profile == 'conservative' and stocks_percentage > 40:
                recommendations.append("Bond Fund: To increase your allocation to fixed income")
                recommendations.append("Dividend Stock Fund: For income generation with moderate growth")
            
            if time_horizon == 'long_term' and bonds_percentage > 30:
                recommendations.append("Target Date Fund: To automatically adjust your allocation as you approach your goal")
            elif time_horizon == 'short_term' and stocks_percentage > 30:
                recommendations.append("Money Market Fund: For capital preservation with short-term goals")
        
        elif visualization_type == "cash_flow":
            # Extract key data points
            income_streams = data.get('income_streams', [])
            expenses = data.get('expenses', [])
            
            if not income_streams and not expenses:
                return "Unable to recommend products without cash flow data."
            
            # Calculate key metrics
            total_income = sum(stream.get('amount', 0) for stream in income_streams)
            total_expenses = sum(expense.get('amount', 0) for expense in expenses)
            net_cash_flow = total_income - total_expenses
            
            # Make recommendations based on cash flow
            if net_cash_flow > 500:
                recommendations.append("Automated Investment Plan: To regularly invest your surplus cash flow")
                recommendations.append("High-Yield Savings Account: To earn more interest on your positive cash flow")
            elif net_cash_flow > 0:
                recommendations.append("Emergency Fund Savings Account: To build a safety net with your positive cash flow")
                recommendations.append("Debt Consolidation Loan: To optimize your debt payments if applicable")
            else:
                recommendations.append("Personal Financial Planning: To help identify ways to improve your cash flow")
                recommendations.append("Balance Transfer Credit Card: To reduce interest costs if you're carrying credit card debt")
        
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
