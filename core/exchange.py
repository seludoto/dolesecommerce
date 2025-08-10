# Example static exchange rates (could be replaced with live rates from an API)
EXCHANGE_RATES = {
    'TZS': 1.0,  # Base currency
    'USD': 0.00039,
    'EUR': 0.00036,
    'GBP': 0.00031,
    'KES': 0.052,
    'PI': 0.000001,
}

def get_exchange_rate(currency):
    return EXCHANGE_RATES.get(currency, 1.0)
