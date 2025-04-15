import base64
import requests
from datetime import datetime
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class MpesaClient:
    def __init__(self, environment='sandbox'):
        self.consumer_key = settings.MPESA_CONSUMER_KEY
        self.consumer_secret = settings.MPESA_CONSUMER_SECRET
        self.passkey = settings.MPESA_PASSKEY
        self.callback_url = settings.MPESA_CALLBACK_URL
        
        self.access_token = self.get_access_token(environment)
        
        if environment == 'production':
            baseUrl = 'https://api.safaricom.co.ke/'
            self.api_url = baseUrl+'mpesa/stkpush/v1/processrequest'
            self.c2b_url = baseUrl+'mpesa/c2b/v1/registerurl'
            self.b2b_url = baseUrl+'mpesa/b2b/v1/registerurl'
            self.b2c_url = baseUrl+'mpesa/b2c/v1/registerurl'
        else:
            baseUrl = 'https://sandbox.safaricom.co.ke/'
            self.api_url = baseUrl+'mpesa/stkpush/v1/processrequest'
            self.c2b_url = baseUrl+'mpesa/c2b/v1/registerurl'
            self.b2b_url = baseUrl+'mpesa/b2b/v1/registerurl'
            self.b2c_url = baseUrl+'mpesa/b2c/v1/registerurl'

    def register_urls(self):
        confirmation_url = settings.MPESA_CONFIRMATION_URL
        validation_url = settings.MPESA_VALIDATION_URL
        short_code = settings.MPESA_C2B_SHORTCODE

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.access_token}'
        }
        payload = {
            "ShortCode": short_code,
            "ResponseType": "Completed",
            "ConfirmationURL": confirmation_url,
            "ValidationURL": validation_url
        }

        try:
            response = requests.post(self.c2b_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()

            response_data = response.json()
            if response_data.get("ResponseDescription") != "Success":
                raise Exception(f"URL registration failed: {response_data}")

            logger.info(f"URL Registration successful: {response_data}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error registering URL: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during URL registration: {e}")

        
    def generate_timestamp(self):
        return datetime.now().strftime("%Y%m%d%H%M%S")

    def generate_password(self, business_short_code):
        timestamp = self.generate_timestamp()
        data_to_encode = business_short_code + self.passkey + timestamp
        encoded_string = base64.b64encode(data_to_encode.encode())
        return encoded_string.decode('utf-8')

    def get_access_token(self, environment):
        if environment == 'production':
            oauth_url = 'https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
        else:
            oauth_url = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'

        try:
            credentials = f"{self.consumer_key}:{self.consumer_secret}"
            encoded = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
            response = requests.get(oauth_url, headers={'Authorization': f'Basic {encoded}'}, timeout=30)
            response.raise_for_status()

            json_response = response.json()
            return json_response['access_token']
        except requests.exceptions.RequestException as e:
            logger.error(f"Error retrieving access token: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error retrieving access token: {e}")
            return None

    def express(self, phone_number, amount):
        """
        Initiates a Lipa Na Mpesa online payment request.

        Parameters:
        phone_number (str): The phone number to be charged.
        amount (float): The amount to be charged.

        Returns:
        dict: The response from the Mpesa API.
        """
        try:
            if not self.access_token:
                raise Exception("Access token is not available")

            headers = {
                'Authorization': 'Bearer ' + self.access_token,
                'Content-Type': 'application/json'
            }
            
            business_shortcode = settings.MPESA_BUSINESS_SHORTCODE
            timestamp = self.generate_timestamp()
            password = self.generate_password(business_shortcode)
            
            payload = {
                "BusinessShortCode": business_shortcode,
                "Password": password,
                "Timestamp": timestamp,
                "TransactionType": "CustomerPayBillOnline",
                "Amount": amount,
                "PartyA": "254792117756",
                "PartyB": business_shortcode,
                "PhoneNumber": phone_number,
                "CallBackURL": self.callback_url,
                "AccountReference": "ExampleCompanyReference",
                "TransactionDesc": "Test Payment"
            }
            
            response = requests.post(self.api_url, headers=headers, json=payload)
            response.raise_for_status()  # Raise an HTTPError for bad responses
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
        except Exception as e:
            return {"error": str(e)}
        
    
    def c2b(self):
        """
        Customer to Business (C2B) transaction
        """
        try:
            if not self.access_token:
                raise Exception("Access token not available")

            # Validate required settings
            if not all([settings.MPESA_C2B_SHORTCODE, settings.MPESA_CONFIRMATION_URL, settings.MPESA_VALIDATION_URL]):
                raise ValueError("C2B configuration is incomplete. Please check your settings.")

            headers = {
                'Authorization': 'Bearer ' + self.access_token,
                'Content-Type': 'application/json'
            }

            payload = {
                "ShortCode": settings.MPESA_C2B_SHORTCODE,
                "ResponseType": "Completed",
                "ConfirmationURL": settings.MPESA_CONFIRMATION_URL,
                "ValidationURL": settings.MPESA_VALIDATION_URL
            }

            response = requests.post(self.c2b_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()

            # Validate response
            response_data = response.json()
            if response_data.get("ResponseDescription") != "Success":
                raise Exception(f"C2B registration failed: {response_data}")

            return response_data
        except requests.exceptions.RequestException as e:
            logger.error(f"Error in C2B transaction: {e}")
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error in C2B transaction: {e}")
            return {"error": str(e)}

    def b2c(self, amount, phone_number, remarks):
        """
        Business to Customer (B2C) transaction
        """
        try:
            if not self.access_token:
                raise Exception("Access token not available")

            # Validate required settings
            if not all([settings.MPESA_INITIATOR_NAME, settings.MPESA_SECURITY_CREDENTIALS, settings.MPESA_BUSINESS_SHORTCODE]):
                raise ValueError("B2C configuration is incomplete. Please check your settings.")

            # Validate phone number format
            if not phone_number.startswith("254") or len(phone_number) != 12:
                raise ValueError("Invalid phone number format. Use the format 2547XXXXXXXX.")

            headers = {
                'Authorization': 'Bearer ' + self.access_token,
                'Content-Type': 'application/json'
            }

            payload = {
                "InitiatorName": settings.MPESA_INITIATOR_NAME,
                "SecurityCredential": settings.MPESA_SECURITY_CREDENTIALS,
                "CommandID": "BusinessPayment",
                "Amount": amount,
                "PartyA": settings.MPESA_BUSINESS_SHORTCODE,
                "PartyB": phone_number,
                "Remarks": remarks,
                "QueueTimeOutURL": settings.MPESA_TIMEOUT_URL,
                "ResultURL": settings.MPESA_RESULT_URL,
                "Occasion": "Payment"
            }

            response = requests.post(self.b2c_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()

            # Validate response
            response_data = response.json()
            if response_data.get("ResponseDescription") != "Success":
                raise Exception(f"B2C transaction failed: {response_data}")

            return response_data
        except requests.exceptions.RequestException as e:
            logger.error(f"Error in B2C transaction: {e}")
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error in B2C transaction: {e}")
            return {"error": str(e)}

