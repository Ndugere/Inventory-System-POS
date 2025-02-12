import base64
import requests
from datetime import datetime
from django.conf import settings

class MpesaClient:
    def __init__(self, environment='sandbox'):
        self.consumer_key = settings.MPESA_CONSUMER_KEY
        self.consumer_secret = settings.MPESA_CONSUMER_SECRET
        self.passkey = settings.MPESA_PASSKEY
        self.callback_url = settings.MPESA_CALLBACK_URL
        
        self.access_token = self.get_access_token(environment)
        
        if environment == 'production':
            baseUrl = 'https://api.safaricom.co.ke/'
            self.api_url = baseUrl+'/mpesa/stkpush/v1/processrequest'
            self.c2b_url = baseUrl+'/mpesa/c2b/v1/registerurl'
            self.b2b_url = baseUrl+'/mpesa/b2b/v1/registerurl'
            self.b2c_url = baseUrl+'/mpesa/b2c/v1/registerurl'
        else:
            baseUrl = 'https://sandbox.safaricom.co.ke'
            self.api_url = baseUrl+'/mpesa/stkpush/v1/processrequest'
            self.c2b_url = baseUrl+'/mpesa/c2b/v1/registerurl'
            self.b2b_url = baseUrl+'/mpesa/b2b/v1/registerurl'
            self.b2c_url = baseUrl+'/mpesa/b2c/v1/registerurl'

    def register_urls(self):
        confirmation_url = settings.MPESA_CONFIRMATION_URL
        validation_url = settings.MPESA_VALIDATION_URL
 
        headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {self.access_token}'
        }
        payload = {
            "ShortCode": 600999,
            "ResponseType": "Completed",
            "ConfirmationURL": confirmation_url,
            "ValidationURL": validation_url,
        }
        
        response = requests.request("POST", 'https://sandbox.safaricom.co.ke/mpesa/c2b/v1/registerurl', headers = headers, data = payload)
        print(f"\nURL Registartion result: {response}\n")
        
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
            response = requests.request('GET', oauth_url, headers = { 'Authorization': f'Basic {encoded}'})            
            
            response.raise_for_status()  # Raise an HTTPError for bad responses
            json_response = response.json()
            return json_response['access_token']
        except requests.exceptions.RequestException as e:
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

            response = requests.post(self.c2b_url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def b2c(self, amount, phone_number, remarks):
        """
        Business to Customer (B2C) transaction
        """
        try:
            if not self.access_token:
                raise Exception("Access token not available")

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

            response = requests.post(self.b2c_url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

   