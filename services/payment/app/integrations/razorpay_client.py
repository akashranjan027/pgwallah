"""
Razorpay integration client for UPI and subscription payments
"""
import hashlib
import hmac
import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any

import razorpay
import structlog
from pydantic import BaseModel

from app.core.config import settings

logger = structlog.get_logger(__name__)


class RazorpayPaymentRequest(BaseModel):
    """Payment request for Razorpay Orders API"""
    amount: Decimal  # In rupees (will be converted to paise)
    currency: str = "INR"
    receipt: str
    notes: Dict[str, str] = {}


class RazorpaySubscriptionRequest(BaseModel):
    """Subscription request for Razorpay Subscriptions API"""
    plan_id: str
    customer_notify: bool = True
    total_count: Optional[int] = None
    addons: List[Dict] = []
    notes: Dict[str, str] = {}


class RazorpayClient:
    """Razorpay API client for payments and subscriptions"""

    def __init__(self):
        self.client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )
        self.webhook_secret = settings.RAZORPAY_WEBHOOK_SECRET

    def _rupees_to_paise(self, amount: Decimal) -> int:
        """Convert rupees to paise (Razorpay uses paise)"""
        return int(amount * 100)

    def _paise_to_rupees(self, amount: int) -> Decimal:
        """Convert paise to rupees"""
        return Decimal(amount) / 100

    async def create_order(
        self,
        amount: Decimal,
        receipt: str,
        notes: Optional[Dict[str, str]] = None,
        currency: str = "INR",
    ) -> Dict[str, Any]:
        """Create Razorpay order for one-time payments"""
        try:
            order_data = {
                "amount": self._rupees_to_paise(amount),
                "currency": currency,
                "receipt": receipt,
                "notes": notes or {},
            }

            logger.info(
                "Creating Razorpay order",
                amount=amount,
                receipt=receipt,
                currency=currency,
            )

            order = self.client.order.create(data=order_data)

            logger.info(
                "Razorpay order created successfully",
                order_id=order["id"],
                amount=amount,
                receipt=receipt,
            )

            return order

        except Exception as e:
            logger.error(
                "Failed to create Razorpay order",
                error=str(e),
                amount=amount,
                receipt=receipt,
            )
            raise

    async def fetch_order(self, order_id: str) -> Dict[str, Any]:
        """Fetch order details from Razorpay"""
        try:
            order = self.client.order.fetch(order_id)
            logger.info("Fetched Razorpay order", order_id=order_id, status=order.get("status"))
            return order
        except Exception as e:
            logger.error("Failed to fetch Razorpay order", order_id=order_id, error=str(e))
            raise

    async def fetch_payment(self, payment_id: str) -> Dict[str, Any]:
        """Fetch payment details from Razorpay"""
        try:
            payment = self.client.payment.fetch(payment_id)
            logger.info(
                "Fetched Razorpay payment",
                payment_id=payment_id,
                status=payment.get("status"),
                method=payment.get("method"),
            )
            return payment
        except Exception as e:
            logger.error("Failed to fetch Razorpay payment", payment_id=payment_id, error=str(e))
            raise

    async def create_subscription(
        self,
        plan_id: str,
        customer_notify: bool = True,
        total_count: Optional[int] = None,
        addons: Optional[List[Dict]] = None,
        notes: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Create Razorpay subscription for recurring payments"""
        try:
            subscription_data = {
                "plan_id": plan_id,
                "customer_notify": customer_notify,
                "notes": notes or {},
            }

            if total_count:
                subscription_data["total_count"] = total_count

            if addons:
                subscription_data["addons"] = addons

            logger.info(
                "Creating Razorpay subscription",
                plan_id=plan_id,
                total_count=total_count,
            )

            subscription = self.client.subscription.create(data=subscription_data)

            logger.info(
                "Razorpay subscription created successfully",
                subscription_id=subscription["id"],
                plan_id=plan_id,
                status=subscription.get("status"),
            )

            return subscription

        except Exception as e:
            logger.error(
                "Failed to create Razorpay subscription",
                error=str(e),
                plan_id=plan_id,
            )
            raise

    async def cancel_subscription(
        self, subscription_id: str, cancel_at_cycle_end: bool = False
    ) -> Dict[str, Any]:
        """Cancel Razorpay subscription"""
        try:
            logger.info(
                "Cancelling Razorpay subscription",
                subscription_id=subscription_id,
                cancel_at_cycle_end=cancel_at_cycle_end,
            )

            subscription = self.client.subscription.cancel(
                subscription_id, {"cancel_at_cycle_end": cancel_at_cycle_end}
            )

            logger.info(
                "Razorpay subscription cancelled",
                subscription_id=subscription_id,
                status=subscription.get("status"),
            )

            return subscription

        except Exception as e:
            logger.error(
                "Failed to cancel Razorpay subscription",
                subscription_id=subscription_id,
                error=str(e),
            )
            raise

    async def create_refund(
        self,
        payment_id: str,
        amount: Optional[Decimal] = None,
        notes: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Create refund for a payment"""
        try:
            refund_data = {"notes": notes or {}}

            if amount:
                refund_data["amount"] = self._rupees_to_paise(amount)

            logger.info(
                "Creating Razorpay refund",
                payment_id=payment_id,
                amount=amount,
            )

            refund = self.client.payment.refund(payment_id, refund_data)

            logger.info(
                "Razorpay refund created successfully",
                refund_id=refund["id"],
                payment_id=payment_id,
                amount=self._paise_to_rupees(refund["amount"]),
            )

            return refund

        except Exception as e:
            logger.error(
                "Failed to create Razorpay refund",
                payment_id=payment_id,
                error=str(e),
            )
            raise

    def verify_webhook_signature(
        self, payload: str, signature: str, webhook_secret: Optional[str] = None
    ) -> bool:
        """Verify Razorpay webhook signature"""
        try:
            secret = webhook_secret or self.webhook_secret
            if not secret:
                logger.warning("No webhook secret configured")
                return False

            expected_signature = hmac.new(
                secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256
            ).hexdigest()

            is_valid = hmac.compare_digest(signature, expected_signature)

            logger.info(
                "Webhook signature verification",
                is_valid=is_valid,
                signature_length=len(signature),
            )

            return is_valid

        except Exception as e:
            logger.error("Webhook signature verification failed", error=str(e))
            return False

    def verify_payment_signature(
        self, order_id: str, payment_id: str, signature: str
    ) -> bool:
        """Verify payment signature from frontend"""
        try:
            params_dict = {
                "razorpay_order_id": order_id,
                "razorpay_payment_id": payment_id,
                "razorpay_signature": signature,
            }

            is_valid = self.client.utility.verify_payment_signature(params_dict)

            logger.info(
                "Payment signature verification",
                order_id=order_id,
                payment_id=payment_id,
                is_valid=is_valid,
            )

            return is_valid

        except Exception as e:
            logger.error(
                "Payment signature verification failed",
                order_id=order_id,
                payment_id=payment_id,
                error=str(e),
            )
            return False

    async def get_upi_intent_url(self, order_id: str, amount: Decimal) -> str:
        """Generate UPI intent URL for direct UPI app opening"""
        # For UPI intent, we'll use the standard UPI URL format
        # This works with PhonePe, GPay, Paytm, etc.
        base_url = "upi://pay"
        params = {
            "pa": settings.UPI_VPA,  # Your UPI VPA
            "pn": "PGwallah",
            "tr": order_id,
            "am": str(amount),
            "cu": "INR",
            "tn": f"PGwallah Payment - {order_id}",
        }

        param_string = "&".join([f"{k}={v}" for k, v in params.items()])
        upi_url = f"{base_url}?{param_string}"

        logger.info(
            "Generated UPI intent URL",
            order_id=order_id,
            amount=amount,
        )

        return upi_url


# Global Razorpay client instance
razorpay_client = RazorpayClient()