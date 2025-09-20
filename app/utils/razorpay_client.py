import os
import hmac
import hashlib
from typing import Optional, Dict, Any

import requests


class RazorpayClient:
    def __init__(self,
                 key_id: Optional[str] = None,
                 key_secret: Optional[str] = None):
        self.key_id = key_id or os.getenv("RAZORPAY_KEY_ID", "")
        self.key_secret = key_secret or os.getenv("RAZORPAY_KEY_SECRET", "")
        self.base_url = "https://api.razorpay.com/v1"
        print("RazorpayClient initialized with:")
        print(self.key_id, self.key_secret)

    def _auth(self):
        return (self.key_id, self.key_secret)

    def create_order(self, amount_paise: int, currency: str = "INR", notes: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        payload = {
            "amount": amount_paise,
            "currency": currency,
            "payment_capture": 1,
            "notes": notes or {},
        }
        resp = requests.post(f"{self.base_url}/orders", auth=self._auth(), json=payload, timeout=20)
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def verify_signature(order_id: str, payment_id: str, signature: str, key_secret: Optional[str] = None) -> bool:
        secret = key_secret or os.getenv("RAZORPAY_KEY_SECRET", "")
        message = f"{order_id}|{payment_id}".encode()
        expected = hmac.new(secret.encode(), msg=message, digestmod=hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)


