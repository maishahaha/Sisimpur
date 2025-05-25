import logging
import json
import requests

logger = logging.getLogger(__name__)


class EmailValidationService:
    def __init__(self, api_key_01, api_key_02):
        self.api_key_01 = api_key_01
        self.api_key_02 = api_key_02

    def is_valid_check_01(self, email):
        url = "http://apilayer.net/api/check"
        params = {
            "access_key": self.api_key_01,
            "email": email,
            "smtp": 1,
            "format": 1,
        }
        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            return data.get("smtp_check", False)
        except requests.RequestException:
            return False

    def is_valid_check_02(self, email):
        url = "https://api.emailvalidation.io/v1/info"
        params = {
            "apikey": self.api_key_02,
            "email": email,
        }
        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            return data.get("smtp_check", False)
        except requests.RequestException:
            return False