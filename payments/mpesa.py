import requests
import base64
import json
import logging
from datetime import datetime
from django.conf import settings

logger = logging.getLogger(__name__)

class MpesaDarajaAPI:
    def __init__(self, consumer_key, consumer_secret, shortcode, passkey, base_url, initiator_name=None, security_credential=None):
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.shortcode = shortcode
        self.passkey = passkey
        self.base_url = base_url
        self.initiator_name = initiator_name or getattr(settings, 'MPESA_INITIATOR_NAME', '')
        self.security_credential = security_credential or getattr(settings, 'MPESA_SECURITY_CREDENTIAL', '')
        self.access_token = self.get_access_token()

    def get_access_token(self):
        """Get OAuth access token from Safaricom"""
        url = f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"
        try:
            response = requests.get(url, auth=(self.consumer_key, self.consumer_secret))
            response.raise_for_status()
            token_data = response.json()
            logger.info("Successfully obtained M-Pesa access token")
            return token_data['access_token']
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get M-Pesa access token: {e}")
            raise

    def stk_push(self, phone_number, amount, account_reference, transaction_desc, callback_url):
        """Initiate STK Push (Customer pays via their phone)"""
        url = f"{self.base_url}/mpesa/stkpush/v1/processrequest"
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
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()
            logger.info(f"STK Push initiated successfully: {result.get('CheckoutRequestID')}")
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"STK Push failed: {e}")
            raise

    def b2c_payment(self, phone_number, amount, remarks, occasion=None):
        """Send money directly to customer phone number (B2C)"""
        url = f"{self.base_url}/mpesa/b2c/v1/paymentrequest"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "InitiatorName": self.initiator_name,
            "SecurityCredential": self.security_credential,
            "CommandID": "BusinessPayment",
            "Amount": amount,
            "PartyA": self.shortcode,
            "PartyB": phone_number,
            "Remarks": remarks,
            "QueueTimeOutURL": f"{settings.SITE_URL}/payments/mpesa/b2c-timeout/",
            "ResultURL": f"{settings.SITE_URL}/payments/mpesa/b2c-result/",
            "Occasion": occasion or remarks[:20]
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()
            logger.info(f"B2C payment initiated: {result.get('ConversationID')}")
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"B2C payment failed: {e}")
            raise

    def c2b_register_urls(self, confirmation_url, validation_url):
        """Register C2B URLs for receiving payments"""
        url = f"{self.base_url}/mpesa/c2b/v1/registerurl"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "ShortCode": self.shortcode,
            "ResponseType": "Completed",
            "ConfirmationURL": confirmation_url,
            "ValidationURL": validation_url
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()
            logger.info("C2B URLs registered successfully")
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"C2B URL registration failed: {e}")
            raise

    def c2b_simulate_payment(self, phone_number, amount, bill_ref_number):
        """Simulate C2B payment for testing"""
        url = f"{self.base_url}/mpesa/c2b/v1/simulate"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "ShortCode": self.shortcode,
            "CommandID": "CustomerPayBillOnline",
            "Amount": amount,
            "Msisdn": phone_number,
            "BillRefNumber": bill_ref_number
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()
            logger.info(f"C2B simulation successful: {result}")
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"C2B simulation failed: {e}")
            raise

    def transaction_status(self, transaction_id):
        """Check the status of a transaction"""
        url = f"{self.base_url}/mpesa/transactionstatus/v1/query"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "Initiator": self.initiator_name,
            "SecurityCredential": self.security_credential,
            "CommandID": "TransactionStatusQuery",
            "TransactionID": transaction_id,
            "PartyA": self.shortcode,
            "IdentifierType": "4",
            "ResultURL": f"{settings.SITE_URL}/payments/mpesa/status-result/",
            "QueueTimeOutURL": f"{settings.SITE_URL}/payments/mpesa/status-timeout/",
            "Remarks": "Transaction status query",
            "Occasion": "Status check"
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()
            logger.info(f"Transaction status query initiated: {result}")
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"Transaction status query failed: {e}")
            raise

    def account_balance(self):
        """Check account balance"""
        url = f"{self.base_url}/mpesa/accountbalance/v1/query"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "Initiator": self.initiator_name,
            "SecurityCredential": self.security_credential,
            "CommandID": "AccountBalance",
            "PartyA": self.shortcode,
            "IdentifierType": "4",
            "Remarks": "Account balance check",
            "QueueTimeOutURL": f"{settings.SITE_URL}/payments/mpesa/balance-timeout/",
            "ResultURL": f"{settings.SITE_URL}/payments/mpesa/balance-result/"
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()
            logger.info("Account balance query initiated")
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"Account balance query failed: {e}")
            raise

    @staticmethod
    def format_phone_number(phone_number):
        """Format phone number to Kenyan format (254XXXXXXXXX)"""
        # Remove any non-digit characters
        phone = ''.join(filter(str.isdigit, phone_number))
        
        # Handle different formats
        if phone.startswith('0'):
            phone = '254' + phone[1:]
        elif phone.startswith('254'):
            pass  # Already in correct format
        elif phone.startswith('+254'):
            phone = phone[1:]
        elif len(phone) == 9:
            phone = '254' + phone
        
        return phone

    @staticmethod
    def validate_phone_number(phone_number):
        """Validate Kenyan phone number format"""
        formatted = MpesaDarajaAPI.format_phone_number(phone_number)
        return len(formatted) == 12 and formatted.startswith('254')


class MpesaPaymentProcessor:
    """High-level M-Pesa payment processor"""
    
    def __init__(self):
        self.api = MpesaDarajaAPI(
            consumer_key=settings.MPESA_CONSUMER_KEY,
            consumer_secret=settings.MPESA_CONSUMER_SECRET,
            shortcode=settings.MPESA_SHORTCODE,
            passkey=settings.MPESA_PASSKEY,
            base_url=settings.MPESA_BASE_URL,
            initiator_name=getattr(settings, 'MPESA_INITIATOR_NAME', ''),
            security_credential=getattr(settings, 'MPESA_SECURITY_CREDENTIAL', '')
        )
    
    def send_money_to_phone(self, phone_number, amount, description="Payment"):
        """Send money directly to a phone number"""
        formatted_phone = self.api.format_phone_number(phone_number)
        
        if not self.api.validate_phone_number(formatted_phone):
            raise ValueError(f"Invalid phone number format: {phone_number}")
        
        return self.api.b2c_payment(
            phone_number=formatted_phone,
            amount=int(amount),
            remarks=description[:50],  # M-Pesa has character limits
            occasion=description[:20]
        )
    
    def request_payment_from_phone(self, phone_number, amount, order_reference, description="Payment Request"):
        """Request payment from a phone number (STK Push)"""
        formatted_phone = self.api.format_phone_number(phone_number)
        
        if not self.api.validate_phone_number(formatted_phone):
            raise ValueError(f"Invalid phone number format: {phone_number}")
        
        callback_url = f"{settings.SITE_URL}/payments/mpesa-callback/"
        
        return self.api.stk_push(
            phone_number=formatted_phone,
            amount=int(amount),
            account_reference=order_reference,
            transaction_desc=description,
            callback_url=callback_url
        )


# Global instance - will be initialized when first accessed
mpesa_processor = None

def get_mpesa_processor():
    """Get the global M-Pesa processor instance, initializing if needed"""
    global mpesa_processor
    if mpesa_processor is None:
        mpesa_processor = MpesaPaymentProcessor()
    return mpesa_processor
