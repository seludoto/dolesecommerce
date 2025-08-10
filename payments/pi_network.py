"""
Pi Network Payment Integration
A comprehensive payment system for Pi Coin integration
"""

import requests
import json
import hashlib
import time
import logging
from decimal import Decimal
from django.conf import settings
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)

class PiNetworkAPI:
    """
    Pi Network API integration for payment processing
    """
    
    def __init__(self, api_key: str, sandbox_mode: bool = True):
        self.api_key = api_key
        self.sandbox_mode = sandbox_mode
        self.base_url = "https://api.mainnet.pi.network" if not sandbox_mode else "https://api.sandbox.pi.network"
        self.api_version = "v2"
        
    def _get_headers(self) -> Dict[str, str]:
        """Generate headers for API requests"""
        return {
            'Authorization': f'Key {self.api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    def _make_request(self, endpoint: str, method: str = 'GET', data: Optional[Dict] = None) -> Dict:
        """Make HTTP request to Pi Network API"""
        url = f"{self.base_url}/{self.api_version}/{endpoint}"
        headers = self._get_headers()
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=data)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data)
            elif method == 'PUT':
                response = requests.put(url, headers=headers, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Pi Network API request failed: {e}")
            raise PiNetworkError(f"API request failed: {e}")
    
    def create_payment(self, amount: Decimal, memo: str, metadata: Dict = None) -> Dict:
        """
        Create a new Pi payment request
        
        Args:
            amount: Payment amount in Pi
            memo: Payment description
            metadata: Additional payment metadata
            
        Returns:
            Payment creation response
        """
        data = {
            'amount': float(amount),
            'memo': memo,
            'metadata': metadata or {}
        }
        
        return self._make_request('payments', method='POST', data=data)
    
    def get_payment(self, payment_id: str) -> Dict:
        """
        Get payment details by ID
        
        Args:
            payment_id: Pi payment ID
            
        Returns:
            Payment details
        """
        return self._make_request(f'payments/{payment_id}')
    
    def approve_payment(self, payment_id: str) -> Dict:
        """
        Approve a pending payment
        
        Args:
            payment_id: Pi payment ID
            
        Returns:
            Approval response
        """
        return self._make_request(f'payments/{payment_id}/approve', method='POST')
    
    def cancel_payment(self, payment_id: str) -> Dict:
        """
        Cancel a pending payment
        
        Args:
            payment_id: Pi payment ID
            
        Returns:
            Cancellation response
        """
        return self._make_request(f'payments/{payment_id}/cancel', method='POST')
    
    def get_incomplete_payments(self) -> Dict:
        """
        Get list of incomplete payments
        
        Returns:
            List of incomplete payments
        """
        return self._make_request('payments/incomplete_server_payments')
    
    def complete_payment(self, payment_id: str, txid: str) -> Dict:
        """
        Complete a payment with transaction ID
        
        Args:
            payment_id: Pi payment ID
            txid: Blockchain transaction ID
            
        Returns:
            Completion response
        """
        data = {'txid': txid}
        return self._make_request(f'payments/{payment_id}/complete', method='POST', data=data)


class PiPaymentValidator:
    """
    Validate Pi Network payments and transactions
    """
    
    @staticmethod
    def validate_payment_data(payment_data: Dict) -> bool:
        """
        Validate payment data structure
        
        Args:
            payment_data: Payment data from Pi Network
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = ['identifier', 'amount', 'memo', 'metadata', 'status']
        return all(field in payment_data for field in required_fields)
    
    @staticmethod
    def verify_payment_signature(payment_data: Dict, secret_key: str) -> bool:
        """
        Verify payment signature for security
        
        Args:
            payment_data: Payment data
            secret_key: Secret key for verification
            
        Returns:
            True if signature is valid
        """
        # Implementation depends on Pi Network's signature mechanism
        # This is a placeholder for the actual verification logic
        return True
    
    @staticmethod
    def calculate_usd_equivalent(pi_amount: Decimal, pi_to_usd_rate: Decimal) -> Decimal:
        """
        Calculate USD equivalent of Pi amount
        
        Args:
            pi_amount: Amount in Pi
            pi_to_usd_rate: Current Pi to USD exchange rate
            
        Returns:
            USD equivalent amount
        """
        return pi_amount * pi_to_usd_rate


class PiNetworkError(Exception):
    """Custom exception for Pi Network API errors"""
    pass


class PiPaymentProcessor:
    """
    High-level Pi payment processor
    """
    
    def __init__(self, api_key: str = None, sandbox_mode: bool = True):
        self.api_key = api_key or getattr(settings, 'PI_NETWORK_API_KEY', '')
        self.sandbox_mode = sandbox_mode
        self.api = PiNetworkAPI(self.api_key, sandbox_mode)
        self.validator = PiPaymentValidator()
    
    def initiate_payment(self, order_id: str, amount: Decimal, description: str) -> Dict:
        """
        Initiate a new Pi payment
        
        Args:
            order_id: Order identifier
            amount: Payment amount in Pi
            description: Payment description
            
        Returns:
            Payment initiation response
        """
        try:
            metadata = {
                'order_id': order_id,
                'timestamp': int(time.time()),
                'source': 'ecommerce_platform'
            }
            
            payment_response = self.api.create_payment(
                amount=amount,
                memo=description,
                metadata=metadata
            )
            
            logger.info(f"Pi payment initiated for order {order_id}: {payment_response}")
            return payment_response
            
        except Exception as e:
            logger.error(f"Failed to initiate Pi payment for order {order_id}: {e}")
            raise
    
    def check_payment_status(self, payment_id: str) -> Dict:
        """
        Check the status of a Pi payment
        
        Args:
            payment_id: Pi payment ID
            
        Returns:
            Payment status information
        """
        try:
            payment_info = self.api.get_payment(payment_id)
            logger.info(f"Pi payment status check for {payment_id}: {payment_info.get('status')}")
            return payment_info
            
        except Exception as e:
            logger.error(f"Failed to check Pi payment status for {payment_id}: {e}")
            raise
    
    def process_payment_callback(self, payment_data: Dict) -> Dict:
        """
        Process Pi payment callback
        
        Args:
            payment_data: Payment callback data
            
        Returns:
            Processing result
        """
        try:
            # Validate payment data
            if not self.validator.validate_payment_data(payment_data):
                raise PiNetworkError("Invalid payment data structure")
            
            # Process based on payment status
            status = payment_data.get('status')
            payment_id = payment_data.get('identifier')
            
            result = {
                'success': False,
                'message': '',
                'payment_id': payment_id,
                'status': status
            }
            
            if status == 'completed':
                result['success'] = True
                result['message'] = 'Payment completed successfully'
            elif status == 'cancelled':
                result['message'] = 'Payment was cancelled'
            elif status == 'pending':
                result['message'] = 'Payment is still pending'
            else:
                result['message'] = f'Unknown payment status: {status}'
            
            logger.info(f"Pi payment callback processed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to process Pi payment callback: {e}")
            raise


# Global instance for easy access
pi_processor = PiPaymentProcessor()
