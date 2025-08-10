from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def currency_display(price, currency='USD'):
    """
    Display price with proper currency symbol and formatting
    """
    if not price:
        return '-'
    
    # Currency symbols and formats
    currency_formats = {
        'USD': ('$', 'before', 2),  # ($123.45)
        'EUR': ('€', 'before', 2),  # (€123.45)
        'KES': ('KSh', 'before', 0),  # (KSh 123)
        'TZS': ('TSh', 'before', 0),  # (TSh 123)
        'PI': ('π', 'before', 4),  # (π 123.4567)
    }
    
    if currency not in currency_formats:
        currency = 'USD'  # fallback
    
    symbol, position, decimals = currency_formats[currency]
    
    # Format the price
    if decimals == 0:
        formatted_price = f"{float(price):,.0f}"
    else:
        formatted_price = f"{float(price):,.{decimals}f}"
    
    # Position the symbol
    if position == 'before':
        if currency in ['KES', 'TZS']:
            return f"{symbol} {formatted_price}"
        else:
            return f"{symbol}{formatted_price}"
    else:
        return f"{formatted_price} {symbol}"

@register.simple_tag
def product_price(product):
    """
    Display product price with proper currency
    """
    if hasattr(product, 'currency') and hasattr(product, 'price'):
        return currency_display(product.price, product.currency)
    elif hasattr(product, 'price'):
        return currency_display(product.price, 'TZS')  # Default to TZS for Tanzania
    return '-'

@register.simple_tag
def product_compare_price(product):
    """
    Display product compare price with proper currency
    """
    if hasattr(product, 'currency') and hasattr(product, 'compare_price') and product.compare_price:
        return currency_display(product.compare_price, product.currency)
    elif hasattr(product, 'compare_price') and product.compare_price:
        return currency_display(product.compare_price, 'TZS')
    return None
