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

def put_dynamodb(table_name, item):
    table = dynamodb_resource.Table(table_name)
    resp = table.put_item(Item=item)
    return resp

def read_dynamodb(table_name, key_condition_expression):
    table = dynamodb_resource.Table(table_name)
    resp = table.query(KeyConditionExpression=key_condition_expression)
    return resp.get('Items', [])

def explain_visualization(data, visualization_type=None, customer_id=None, additional_context=None):
    """Main function to explain a financial visualization based on its underlying data"""
    try:
        # Parse data if it's a string
        if isinstance(data, str):
            data = json.loads(data)
            
        # If visualization_type is not provided, try to get it from the data
        if not visualization_type:
            visualization_type = data.get('visualization_type')
        
        # Route to the appropriate explanation function based on visualization type
        if visualization_type == 'spending_trend':
            return explain_spending_trend(data, customer_id, additional_context)
        elif visualization_type == 'investment_allocation':
            return explain_investment_allocation(data, customer_id, additional_context)
        elif visualization_type == 'cash_flow':
            return explain_cash_flow(data, customer_id, additional_context)
        elif visualization_type == 'budget_performance':
            return explain_budget_performance(data, customer_id, additional_context)
        else:
            return f"I don't know how to explain a {visualization_type} visualization yet."
    except Exception as e:
        return f"Error explaining visualization: {str(e)}"


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


def explain_investment_allocation(data, customer_id=None, additional_context=None):
    """Generate explanation for an investment allocation visualization"""
    try:
        # Parse data if it's a string
        if isinstance(data, str):
            data = json.loads(data)
            
        # Extract key data points
        allocations = data.get('allocations', [])
        total_investment = data.get('total_investment', 0)
        risk_profile = data.get('risk_profile', 'moderate')
        time_horizon = data.get('time_horizon', 'medium_term')
        
        if not allocations:
            return "This investment allocation visualization doesn't contain any allocation data to analyze."
        
        # Sort allocations by percentage (descending)
        allocations.sort(key=lambda x: x.get('percentage', 0), reverse=True)
        
        # Calculate key metrics
        total_percentage = sum(alloc.get('percentage', 0) for alloc in allocations)
        
        # Categorize allocations by risk level
        high_risk = []
        moderate_risk = []
        low_risk = []
        
        for alloc in allocations:
            asset_class = alloc.get('asset_class', '').lower()
            percentage = alloc.get('percentage', 0)
            
            if asset_class in ['stocks', 'equities', 'international stocks', 'emerging markets', 'small cap', 'cryptocurrencies', 'alternatives']:
                high_risk.append((asset_class, percentage))
            elif asset_class in ['bonds', 'corporate bonds', 'municipal bonds', 'balanced funds', 'real estate', 'reits']:
                moderate_risk.append((asset_class, percentage))
            else:  # cash, treasuries, cds, money market
                low_risk.append((asset_class, percentage))
        
        high_risk_total = sum(pct for _, pct in high_risk)
        moderate_risk_total = sum(pct for _, pct in moderate_risk)
        low_risk_total = sum(pct for _, pct in low_risk)
        
        # Generate explanation
        explanation = f"This investment allocation visualization for customer {customer_id} shows how their portfolio of ${total_investment:,.2f} is distributed across different asset classes.\n\n"
        
        # Overall allocation
        explanation += "Asset allocation breakdown:\n"
        for alloc in allocations:
            asset_class = alloc.get('asset_class', 'Unknown')
            percentage = alloc.get('percentage', 0)
            amount = total_investment * percentage / 100 if total_investment else 0
            explanation += f"- {asset_class}: {percentage}% (${amount:,.2f})\n"
        explanation += "\n"
        
        # Risk profile analysis
        explanation += "Risk profile analysis:\n"
        explanation += f"- High-risk assets: {high_risk_total}%\n"
        explanation += f"- Moderate-risk assets: {moderate_risk_total}%\n"
        explanation += f"- Low-risk assets: {low_risk_total}%\n\n"
        
        # Insights and recommendations
        explanation += "Key insights:\n"
        
        # Risk alignment
        if risk_profile == 'aggressive' and high_risk_total < 60:
            explanation += "- The current allocation has less high-risk assets than expected for an aggressive risk profile.\n"
            explanation += "- Consider increasing exposure to stocks or other growth assets if appropriate.\n"
        elif risk_profile == 'conservative' and high_risk_total > 40:
            explanation += "- The current allocation has more high-risk assets than expected for a conservative risk profile.\n"
            explanation += "- Consider reducing exposure to stocks in favor of bonds or cash equivalents.\n"
        elif risk_profile == 'moderate' and (high_risk_total < 30 or high_risk_total > 70):
            explanation += "- The current allocation may not be well-aligned with a moderate risk profile.\n"
            explanation += "- Consider rebalancing to achieve better risk-return alignment.\n"
        else:
            explanation += "- The current allocation appears to be aligned with the stated risk profile.\n"
        
        # Diversification
        if len(allocations) < 4:
            explanation += "- The portfolio has limited diversification across asset classes.\n"
            explanation += "- Consider adding more asset classes to reduce risk through diversification.\n"
        elif max(alloc.get('percentage', 0) for alloc in allocations) > 50:
            explanation += "- There is significant concentration in a single asset class.\n"
            explanation += "- Consider diversifying further to reduce concentration risk.\n"
        else:
            explanation += "- The portfolio shows good diversification across multiple asset classes.\n"
        
        return explanation
    
    except Exception as e:
        return f"Error analyzing investment allocation visualization: {str(e)}"


def explain_cash_flow(data, customer_id=None, additional_context=None):
    """Generate explanation for a cash flow visualization"""
    try:
        # Parse data if it's a string
        if isinstance(data, str):
            data = json.loads(data)
            
        # Extract key data points
        months = data.get('months', [])
        income = data.get('income', [])
        expenses = data.get('expenses', [])
        time_period = data.get('time_period', '3_months')
        
        if not months or not income or not expenses:
            return "This cash flow visualization doesn't contain enough data to analyze."
        
        # Calculate key metrics
        total_income = sum(income)
        total_expenses = sum(expenses)
        net_cash_flow = total_income - total_expenses
        average_income = total_income / len(income) if income else 0
        average_expenses = total_expenses / len(expenses) if expenses else 0
        average_net = average_income - average_expenses
        
        # Calculate monthly net cash flows
        monthly_net = [inc - exp for inc, exp in zip(income, expenses)]
        
        # Determine cash flow trend
        trend = "stable"
        if len(monthly_net) > 1:
            if monthly_net[-1] > monthly_net[0] * 1.1:  # 10% increase
                trend = "improving"
            elif monthly_net[-1] < monthly_net[0] * 0.9:  # 10% decrease
                trend = "declining"
        
        # Generate explanation
        explanation = f"This cash flow visualization for customer {customer_id} shows their income and expenses over the past {time_period.replace('_', ' ')}.\n\n"
        
        # Overall summary
        explanation += "Overall summary:\n"
        explanation += f"- Total income: ${total_income:,.2f}\n"
        explanation += f"- Total expenses: ${total_expenses:,.2f}\n"
        explanation += f"- Net cash flow: ${net_cash_flow:,.2f}\n"
        explanation += f"- Average monthly income: ${average_income:,.2f}\n"
        explanation += f"- Average monthly expenses: ${average_expenses:,.2f}\n"
        explanation += f"- Average monthly net cash flow: ${average_net:,.2f}\n\n"
        
        # Monthly breakdown
        explanation += "Monthly breakdown:\n"
        for i, month in enumerate(months):
            explanation += f"- {month}: Income ${income[i]:,.2f}, Expenses ${expenses[i]:,.2f}, Net ${monthly_net[i]:,.2f}\n"
        explanation += "\n"
        
        # Insights and recommendations
        explanation += "Key insights:\n"
        
        # Cash flow status
        if net_cash_flow > 0:
            explanation += "- Positive overall cash flow, which is good for financial health.\n"
            if average_net > 1000:
                explanation += "- Strong monthly savings potential that could be directed toward investments or debt reduction.\n"
            else:
                explanation += "- Consider opportunities to increase savings rate for greater financial security.\n"
        elif net_cash_flow < 0:
            explanation += "- Negative overall cash flow, which may indicate financial stress.\n"
            explanation += "- Recommend reviewing expenses to identify potential areas for reduction.\n"
            if abs(net_cash_flow) > 0.2 * total_income:  # If deficit is more than 20% of income
                explanation += "- The cash flow deficit is significant and requires immediate attention.\n"
        else:
            explanation += "- Balanced cash flow (income equals expenses).\n"
            explanation += "- While this maintains stability, consider creating a surplus for savings and emergencies.\n"
        
        # Trend analysis
        if trend == "improving":
            explanation += "- Cash flow is improving over the period, which is a positive sign.\n"
            explanation += "- Continue the current financial management approach.\n"
        elif trend == "declining":
            explanation += "- Cash flow is declining over the period, which may be a concern.\n"
            explanation += "- Investigate the causes of this decline and take corrective action if needed.\n"
        else:
            explanation += "- Cash flow is relatively stable over the period.\n"
            explanation += "- Regular monitoring will help maintain this stability.\n"
        
        return explanation
    
    except Exception as e:
        return f"Error analyzing cash flow visualization: {str(e)}"


def explain_budget_performance(data, customer_id=None, additional_context=None):
    """Generate explanation for a budget performance visualization"""
    try:
        # Parse data if it's a string
        if isinstance(data, str):
            data = json.loads(data)
            
        # Extract key data points
        categories = data.get('categories', [])
        planned = data.get('planned', [])
        actual = data.get('actual', [])
        time_period = data.get('time_period', 'current_month')
        
        if not categories or not planned or not actual:
            return "This budget performance visualization doesn't contain enough data to analyze."
        
        # Calculate key metrics
        total_planned = sum(planned)
        total_actual = sum(actual)
        total_variance = total_actual - total_planned
        total_variance_pct = (total_variance / total_planned * 100) if total_planned else 0
        
        # Calculate category variances
        variances = [a - p for a, p in zip(actual, planned)]
        variance_pcts = [(v / p * 100) if p else 0 for v, p in zip(variances, planned)]
        
        # Identify categories with significant variances
        over_budget = [(categories[i], actual[i], planned[i], variances[i], variance_pcts[i]) 
                      for i in range(len(categories)) if variance_pcts[i] > 10]  # Over by 10%
        under_budget = [(categories[i], actual[i], planned[i], variances[i], variance_pcts[i]) 
                       for i in range(len(categories)) if variance_pcts[i] < -10]  # Under by 10%
        
        # Sort by absolute variance percentage (descending)
        over_budget.sort(key=lambda x: x[4], reverse=True)
        under_budget.sort(key=lambda x: abs(x[4]), reverse=True)
        
        # Generate explanation
        explanation = f"This budget performance visualization for customer {customer_id} shows their planned versus actual spending for {time_period.replace('_', ' ')}.\n\n"
        
        # Overall summary
        explanation += "Overall budget summary:\n"
        explanation += f"- Total planned spending: ${total_planned:,.2f}\n"
        explanation += f"- Total actual spending: ${total_actual:,.2f}\n"
        explanation += f"- Total variance: ${total_variance:,.2f} ({total_variance_pct:+.1f}%)\n\n"
        
        # Category breakdown
        explanation += "Category breakdown:\n"
        for i, category in enumerate(categories):
            explanation += f"- {category}: Planned ${planned[i]:,.2f}, Actual ${actual[i]:,.2f}, Variance ${variances[i]:,.2f} ({variance_pcts[i]:+.1f}%)\n"
        explanation += "\n"
        
        # Insights and recommendations
        explanation += "Key insights:\n"
        
        # Overall budget status
        if total_variance > 0:
            explanation += f"- Overall spending is ${total_variance:,.2f} ({total_variance_pct:+.1f}%) over budget.\n"
            if total_variance_pct > 20:
                explanation += "- This represents a significant budget overage that requires attention.\n"
            elif total_variance_pct > 10:
                explanation += "- This moderate budget overage suggests a need for closer expense monitoring.\n"
            else:
                explanation += "- This slight budget overage is within a reasonable range but worth monitoring.\n"
        elif total_variance < 0:
            explanation += f"- Overall spending is ${abs(total_variance):,.2f} ({total_variance_pct:+.1f}%) under budget.\n"
            if total_variance_pct < -20:
                explanation += "- This significant underspending might indicate delayed purchases or conservative estimates.\n"
            else:
                explanation += "- This underspending represents good financial discipline.\n"
        else:
            explanation += "- Overall spending is exactly on budget.\n"
        
        # Categories significantly over budget
        if over_budget:
            explanation += "\nCategories significantly over budget:\n"
            for category, actual_amt, planned_amt, variance, variance_pct in over_budget:
                explanation += f"- {category}: ${variance:,.2f} ({variance_pct:+.1f}%) over planned ${planned_amt:,.2f}\n"
            explanation += "\nRecommendations for over-budget categories:\n"
            explanation += "- Review these categories to understand the causes of overspending.\n"
            explanation += "- Consider adjusting future budgets or implementing spending controls.\n"
        
        # Categories significantly under budget
        if under_budget:
            explanation += "\nCategories significantly under budget:\n"
            for category, actual_amt, planned_amt, variance, variance_pct in under_budget:
                explanation += f"- {category}: ${abs(variance):,.2f} ({variance_pct:+.1f}%) under planned ${planned_amt:,.2f}\n"
            explanation += "\nConsiderations for under-budget categories:\n"
            explanation += "- Determine if underspending represents savings or delayed expenses.\n"
            explanation += "- Consider reallocating budget from these categories if the trend continues.\n"
        
        return explanation
    
    except Exception as e:
        return f"Error analyzing budget performance visualization: {str(e)}"


def recommend_financial_products(customer_profile, visualization_data=None, additional_context=None):
    """Recommend financial products based on customer profile and visualization data"""
    try:
        # Parse customer profile if it's a string
        if isinstance(customer_profile, str):
            customer_profile = json.loads(customer_profile)
            
        # Parse visualization data if provided and it's a string
        if visualization_data and isinstance(visualization_data, str):
            visualization_data = json.loads(visualization_data)
        
        # Extract customer profile information
        age = customer_profile.get('age', 35)
        income = customer_profile.get('income', 75000)
        credit_score = customer_profile.get('credit_score', 700)
        risk_tolerance = customer_profile.get('risk_tolerance', 'moderate')
        financial_goals = customer_profile.get('financial_goals', [])
        existing_products = customer_profile.get('existing_products', [])
        life_stage = customer_profile.get('life_stage', 'adult')
        net_worth = customer_profile.get('net_worth', income * 2)
        debt_to_income = customer_profile.get('debt_to_income', 0.3)
        
        # Initialize recommendations
        recommendations = []
        explanations = []
        
        # Helper function to check if a product is already owned
        def has_product(product_type):
            return any(product.get('type', '').lower() == product_type.lower() for product in existing_products)
        
        # Check for basic financial products everyone should have
        if not has_product('checking account'):
            recommendations.append({
                'product_type': 'Checking Account',
                'product_name': 'Everyday Checking',
                'priority': 'High'
            })
            explanations.append("A checking account is essential for day-to-day transactions and bill payments.")
        
        if not has_product('savings account') and income > 0:
            recommendations.append({
                'product_type': 'Savings Account',
                'product_name': 'High-Yield Savings',
                'priority': 'High'
            })
            explanations.append("A high-yield savings account provides a safe place for emergency funds while earning interest.")
        
        # Credit products based on credit score
        if not has_product('credit card') and credit_score >= 650:
            if credit_score >= 750:
                card_type = 'Premium Rewards Card'
                explanation = "With an excellent credit score, you qualify for our premium rewards card with enhanced benefits."
            elif credit_score >= 700:
                card_type = 'Cash Back Card'
                explanation = "Your good credit score qualifies you for a competitive cash back credit card."
            else:
                card_type = 'Secured Credit Card'
                explanation = "This card can help you continue building your credit history with responsible use."
                
            recommendations.append({
                'product_type': 'Credit Card',
                'product_name': card_type,
                'priority': 'Medium'
            })
            explanations.append(explanation)
        
        # Investment products based on risk tolerance and life stage
        if not has_product('investment account'):
            if risk_tolerance == 'aggressive' and age < 50:
                investment_type = 'Growth Stock Portfolio'
                explanation = "Based on your aggressive risk tolerance and age, a growth-focused investment strategy may align with your long-term goals."
            elif risk_tolerance == 'conservative' or age >= 60:
                investment_type = 'Income & Dividend Portfolio'
                explanation = "A more conservative investment approach focused on income generation and capital preservation."
            else:  # moderate risk tolerance
                investment_type = 'Balanced Fund Portfolio'
                explanation = "A balanced investment approach provides a mix of growth potential and risk management."
                
            recommendations.append({
                'product_type': 'Investment Account',
                'product_name': investment_type,
                'priority': 'Medium'
            })
            explanations.append(explanation)
        
        # Loan products based on needs and life stage
        if life_stage == 'young adult' and not has_product('student loan') and 'education' in financial_goals:
            recommendations.append({
                'product_type': 'Student Loan',
                'product_name': 'Education Financing',
                'priority': 'Medium'
            })
            explanations.append("Education financing options to help achieve your educational goals with competitive rates.")
        
        if (life_stage in ['adult', 'family'] and not has_product('mortgage') and 
            'home_ownership' in financial_goals and income >= 50000 and credit_score >= 680):
            recommendations.append({
                'product_type': 'Mortgage',
                'product_name': 'Home Buyer Mortgage',
                'priority': 'Medium'
            })
            explanations.append("Financing options for home purchase with competitive rates based on your solid financial profile.")
        
        # Retirement planning
        if not has_product('retirement account') and age < 65:
            if income > 100000 and not has_product('401k'):
                retirement_type = 'Solo 401(k)'
                explanation = "A tax-advantaged retirement account with higher contribution limits for high-income individuals."
            else:
                retirement_type = 'IRA Account'
                explanation = "A tax-advantaged retirement account to help secure your financial future."
                
            recommendations.append({
                'product_type': 'Retirement Account',
                'product_name': retirement_type,
                'priority': 'High'
            })
            explanations.append(explanation)
        
        # Insurance products based on life stage and needs
        if life_stage in ['family', 'adult'] and not has_product('life insurance') and income > 40000:
            recommendations.append({
                'product_type': 'Life Insurance',
                'product_name': 'Term Life Protection',
                'priority': 'Medium'
            })
            explanations.append("Life insurance provides financial protection for your loved ones and peace of mind for you.")
        
        # Format the response
        if not recommendations:
            return "Based on the customer profile, there are no additional financial products to recommend at this time. The customer appears to have a comprehensive suite of financial products that align with their needs."
        
        response = "Based on the customer profile, here are personalized financial product recommendations:\n\n"
        
        # Sort recommendations by priority
        priority_order = {"High": 0, "Medium": 1, "Low": 2}
        recommendations.sort(key=lambda x: priority_order.get(x.get('priority', 'Low'), 3))
        
        for i, rec in enumerate(recommendations):
            response += f"{i+1}. {rec['product_name']} ({rec['product_type']})\n"
            response += f"   Priority: {rec['priority']}\n"
            response += f"   Rationale: {explanations[i]}\n\n"
        
        response += "These recommendations are based on the provided customer profile and should be discussed with the customer to ensure they align with their current financial situation and goals."
        
        return response
    
    except Exception as e:
        return f"Error generating financial product recommendations: {str(e)}"


def lambda_handler(event, context):
    print(event)
    
    # name of the function that should be invoked
    function = event.get('function', '')

    # parameters to invoke function with
    parameters = event.get('parameters', [])
    customer_id = get_named_parameter(event, "customer_id")
    data = get_named_parameter(event, "data")
    additional_context = get_named_parameter(event, "additional_context")

    # Call the appropriate function based on the function name
    if function == 'explain_spending_trend':
        result = explain_spending_trend(data, customer_id, additional_context)
    elif function == 'explain_investment_allocation':
        result = explain_investment_allocation(data, customer_id, additional_context)
    elif function == 'explain_cash_flow':
        result = explain_cash_flow(data, customer_id, additional_context)
    elif function == 'explain_budget_performance':
        result = explain_budget_performance(data, customer_id, additional_context)
    elif function == 'explain_visualization':
        visualization_type = get_named_parameter(event, "visualization_type")
        result = explain_visualization(data, visualization_type, customer_id, additional_context)
    elif function == 'recommend_financial_products':
        customer_profile = data  # The data parameter contains the customer profile
        visualization_data = get_named_parameter(event, "visualization_data")
        result = recommend_financial_products(customer_profile, visualization_data, additional_context)
    else:
        # Default response for functions not yet implemented
        result = f"Function '{function}' not yet implemented in this version."

    response = populate_function_response(event, result)
    print(response)
    return response
