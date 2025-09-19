"""
Receipt generation and storage utilities
"""
import io
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

import boto3
import structlog
from botocore.client import Config
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.payment import Payment, PaymentIntent

logger = structlog.get_logger(__name__)


class ReceiptGenerator:
    """Receipt generator for payment confirmations"""

    def __init__(self):
        # Initialize MinIO/S3 client
        self.s3_client = boto3.client(
            's3',
            endpoint_url=f"{'https' if settings.MINIO_SECURE else 'http'}://{settings.MINIO_ENDPOINT}",
            aws_access_key_id=settings.MINIO_ACCESS_KEY,
            aws_secret_access_key=settings.MINIO_SECRET_KEY,
            config=Config(signature_version='s3v4'),
            region_name='us-east-1',  # MinIO default
        )

    async def generate_payment_receipt(self, payment_id: uuid.UUID) -> Optional[str]:
        """Generate and store payment receipt"""
        
        async with AsyncSessionLocal() as db:
            try:
                # Fetch payment details
                stmt = select(Payment).where(Payment.id == payment_id)
                result = await db.execute(stmt)
                payment = result.scalar_one_or_none()

                if not payment:
                    logger.error("Payment not found for receipt generation", payment_id=str(payment_id))
                    return None

                # Fetch payment intent for additional details
                stmt = select(PaymentIntent).where(PaymentIntent.id == payment.payment_intent_id)
                result = await db.execute(stmt)
                payment_intent = result.scalar_one_or_none()

                if not payment_intent:
                    logger.error("Payment intent not found", payment_intent_id=str(payment.payment_intent_id))
                    return None

                # Generate receipt content
                receipt_content = self._generate_receipt_html(payment, payment_intent)
                
                # Upload to MinIO/S3
                receipt_url = await self._upload_receipt(payment_id, receipt_content)
                
                # Update payment with receipt URL
                payment.receipt_url = receipt_url
                await db.commit()

                logger.info(
                    "Receipt generated successfully",
                    payment_id=str(payment_id),
                    receipt_url=receipt_url,
                )

                return receipt_url

            except Exception as e:
                logger.error(
                    "Failed to generate receipt",
                    payment_id=str(payment_id),
                    error=str(e),
                )
                return None

    def _generate_receipt_html(self, payment: Payment, payment_intent: PaymentIntent) -> str:
        """Generate HTML receipt content"""
        
        receipt_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Payment Receipt - PGwallah</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
        .receipt {{ max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; border-bottom: 2px solid #2563eb; padding-bottom: 20px; margin-bottom: 30px; }}
        .logo {{ color: #2563eb; font-size: 28px; font-weight: bold; margin-bottom: 10px; }}
        .title {{ color: #1f2937; font-size: 18px; font-weight: 600; }}
        .section {{ margin-bottom: 25px; }}
        .section h3 {{ color: #374151; font-size: 16px; margin-bottom: 10px; border-bottom: 1px solid #e5e7eb; padding-bottom: 5px; }}
        .detail-row {{ display: flex; justify-content: space-between; margin-bottom: 8px; }}
        .detail-label {{ color: #6b7280; font-weight: 500; }}
        .detail-value {{ color: #1f2937; font-weight: 600; }}
        .amount {{ font-size: 24px; color: #059669; font-weight: bold; }}
        .status {{ padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; text-transform: uppercase; }}
        .status.captured {{ background-color: #d1fae5; color: #047857; }}
        .footer {{ text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb; color: #6b7280; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="receipt">
        <div class="header">
            <div class="logo">PGwallah</div>
            <div class="title">Payment Receipt</div>
        </div>

        <div class="section">
            <h3>Transaction Details</h3>
            <div class="detail-row">
                <span class="detail-label">Receipt Number:</span>
                <span class="detail-value">{payment.razorpay_payment_id}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Date & Time:</span>
                <span class="detail-value">{payment.processed_at.strftime('%d %B %Y, %I:%M %p')}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Payment Method:</span>
                <span class="detail-value">{payment.method.upper() if payment.method else 'UPI'}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Status:</span>
                <span class="status captured">Successful</span>
            </div>
        </div>

        <div class="section">
            <h3>Payment Information</h3>
            <div class="detail-row">
                <span class="detail-label">Purpose:</span>
                <span class="detail-value">{payment_intent.purpose.title()}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Description:</span>
                <span class="detail-value">{payment_intent.description or 'PG Payment'}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Amount Paid:</span>
                <span class="detail-value amount">₹{payment.amount:,.2f}</span>
            </div>
            {f'<div class="detail-row"><span class="detail-label">Processing Fee:</span><span class="detail-value">₹{payment.fee:,.2f}</span></div>' if payment.fee else ''}
            {f'<div class="detail-row"><span class="detail-label">Tax:</span><span class="detail-value">₹{payment.tax:,.2f}</span></div>' if payment.tax else ''}
        </div>

        <div class="section">
            <h3>Customer Information</h3>
            <div class="detail-row">
                <span class="detail-label">Tenant ID:</span>
                <span class="detail-value">{payment.tenant_id}</span>
            </div>
            {f'<div class="detail-row"><span class="detail-label">Booking ID:</span><span class="detail-value">{payment_intent.booking_id}</span></div>' if payment_intent.booking_id else ''}
        </div>

        <div class="footer">
            <p>This is a system-generated receipt for your PGwallah payment.</p>
            <p>For any queries, please contact support at support@pgwallah.com</p>
            <p>Generated on {datetime.utcnow().strftime('%d %B %Y at %I:%M %p UTC')}</p>
        </div>
    </div>
</body>
</html>
        """
        
        return receipt_html.strip()

    async def _upload_receipt(self, payment_id: uuid.UUID, content: str) -> str:
        """Upload receipt to MinIO/S3 and return URL"""
        
        try:
            # Ensure bucket exists
            try:
                self.s3_client.head_bucket(Bucket=settings.MINIO_BUCKET_RECEIPTS)
            except:
                self.s3_client.create_bucket(Bucket=settings.MINIO_BUCKET_RECEIPTS)

            # Generate unique filename
            filename = f"receipts/{datetime.utcnow().strftime('%Y/%m')}/receipt_{payment_id}.html"
            
            # Upload file
            self.s3_client.put_object(
                Bucket=settings.MINIO_BUCKET_RECEIPTS,
                Key=filename,
                Body=content.encode('utf-8'),
                ContentType='text/html',
                CacheControl='max-age=86400',  # 24 hours
                ContentDisposition=f'inline; filename="receipt_{payment_id}.html"',
            )

            # Generate URL (for MinIO, this would be a direct URL)
            receipt_url = f"{'https' if settings.MINIO_SECURE else 'http'}://{settings.MINIO_ENDPOINT}/{settings.MINIO_BUCKET_RECEIPTS}/{filename}"
            
            logger.info(
                "Receipt uploaded successfully",
                payment_id=str(payment_id),
                filename=filename,
            )

            return receipt_url

        except Exception as e:
            logger.error(
                "Failed to upload receipt",
                payment_id=str(payment_id),
                error=str(e),
            )
            raise


# Global receipt generator
receipt_generator = ReceiptGenerator()


async def generate_receipt(payment_id: uuid.UUID):
    """Background task to generate receipt"""
    try:
        await receipt_generator.generate_payment_receipt(payment_id)
    except Exception as e:
        logger.error(
            "Background receipt generation failed",
            payment_id=str(payment_id),
            error=str(e),
        )