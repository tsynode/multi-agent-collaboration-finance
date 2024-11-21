import json
import yfinance as yf 

def get_named_parameter(event, name):
    return next(item for item in event['parameters'] if item['name'] == name)['value']
    
def populate_function_response(event, response_body):
    return {'response': {'actionGroup': event['actionGroup'], 'function': event['function'],
                'functionResponse': {'responseBody': {'TEXT': {'body': str(response_body)}}}}}

def get_price_history(ticker):
    # lookup stock price
    stock = yf.Ticker(ticker)

    # get the price history for past 1 month
    hist = stock.history(period="1mo")

    # convert the price history to JSON format. Make date and timestamps be human readable strings.
    hist = hist.reset_index().to_json(orient="split", index=False, date_format="iso")  
    return hist  

def lambda_handler(event, context):
    print(event)
    
    function = event['function']

    ticker = get_named_parameter(event, 'ticker')

    if function == 'stock_data_lookup':
        hist = get_price_history(ticker)
        result = f"Price history for last 1 month for ticker: {ticker} is as follows:\n{str(hist)}"

    response = populate_function_response(event, result)
    print(response)
    return response
