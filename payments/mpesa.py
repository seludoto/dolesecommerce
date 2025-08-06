import requests
import base64
from django.conf import settings

class MpesaDarajaAPI:
    def __init__(self, consumer_key, consumer_secret, shortcode, passkey, base_url):
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.shortcode = shortcode
        self.passkey = passkey
        self.base_url = base_url
        self.access_token = self.get_access_token()

    def get_access_token(self):
        url = f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"
        response = requests.get(url, auth=(self.consumer_key, self.consumer_secret))
        response.raise_for_status()
        return response.json()['access_token']

    def stk_push(self, phone_number, amount, account_reference, transaction_desc, callback_url):
        url = f"{self.base_url}/mpesa/stkpush/v1/processrequest"
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password = base64.b64encode(f"{self.shortcode}{self.passkey}{timestamp}".encode()).decode()
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "BusinessShortCode": self.shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount,
            "PartyA": phone_number,
            "PartyB": self.shortcode,
            "PhoneNumber": phone_number,
            "CallBackURL": callback_url,
            "AccountReference": account_reference,
            "TransactionDesc": transaction_desc
        }
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
