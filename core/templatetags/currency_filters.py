from django import template
from core.exchange import get_exchange_rate

register = template.Library()

@register.filter
def convert_currency(price, currency):
    try:
        price = float(price)
        rate = get_exchange_rate(currency)
        return f"{currency} {price * rate:.2f}"
    except Exception:
        return price
