import requests
import logging

_logger = logging.getLogger(__name__)


class LoanAPI:
    def __init__(self, base_url):
        self.base_url = base_url
        self.headers = {
            'Content-Type': 'application/json',
            'Connection': 'close'
        }

    def create_bill(self, data):
        url = f"{self.base_url}/bill/create"
        with requests.Session() as session:
            session.keep_alive = False
            try:
                res = session.post(url, data={"bill_data": data}, headers=self.headers)
                res = res.json()
                return res.get("id")
            except Exception as e:
                _logger.error(f"[LoanMarketAPI]Error creating bill: {e}")
                return False
            
    def update_bill(self, data):
        url = f"{self.base_url}/bill/update"
        with requests.Session() as session:
            session.keep_alive = False
            try:
                res = session.post(url, json={"bill_data": data}, headers=self.headers)
            except Exception as e:
                _logger.error(f"[LoanMarketAPI]Error updating bill: {e}")
                return False

    def update_user_profile(self, data):
        url = f"{self.base_url}/user/update_derive_user_profile"
        with requests.Session() as session:
            session.keep_alive = False
            try:
                session.post(url, json={"user_data": data}, headers=self.headers)
                return True
            except Exception as e:
                _logger.error(f"[LoanMarketAPI]Error updating bill: {e}")
                return False
