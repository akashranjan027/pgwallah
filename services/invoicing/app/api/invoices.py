"""
Invoice API endpoints with GST compliance and PDF generation
"""
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional

import structlog
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models.invoice import Invoice, InvoiceItem, InvoiceSequence, InvoiceStatus, InvoiceType, TaxType
from app.schemas.invoice import (
    CreateInvoiceRequest,
    InvoiceResponse,
    MonthlyInvoiceRequest,
    InvoiceListResponse,
)
from app.utils.pdf_generator import generate_invoice_pdf
from app.utils.email_sender import send_invoice_email
from app.utils.events import publish_invoice_event

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.post("/", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    request: CreateInvoiceRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Create new invoice manually"""
    
    logger.info(
        "Creating invoice",
        tenant_id=str(request.tenant_id),
        invoice_type=request.invoice_type,
        items_count=len(request.items),
    )

    # Generate invoice number
    current_fy = get_current_financial_year()
    stmt = select(InvoiceSequence).where(InvoiceSequence.financial_year == current_fy)
    result = await db.execute(stmt)
    sequence = result.scalar_one_or_none()
    
    if not sequence:
        sequence = InvoiceSequence(financial_year=current_fy)
        db.add(sequence)
        await db.flush()
    
    invoice_number = sequence.generate_invoice_number()

    # Calculate totals
    subtotal = Decimal('0.00')
    tax_amount = Decimal('0.00')

    # Create invoice
    invoice = Invoice(
        invoice_number=invoice_number,
        tenant_id=request.tenant_id,
        booking_id=request.booking_id,
        invoice_type=request.invoice_type,
        period_start=request.period_start,
        period_end=request.period_end,
        invoice_date=request.invoice_date or datetime.utcnow(),
        due_date=request.due_date,
        gstin=request.gstin,
        place_of_supply=request.place_of_supply or "Karnataka",
        notes=request.notes,
    )

    # Create invoice items
    for item_request in request.items:
        line_total = item_request.quantity * item_request.unit_price
        
        # Calculate tax based on type
        item_tax_amount = Decimal('0.00')
        if item_request.tax_type != TaxType.EXEMPT and item_request.tax_rate > 0:
            item_tax_amount = line_total * item_request.tax_rate / 100

        invoice_item = InvoiceItem(
            description=item_request.description,
            quantity=item_request.quantity,
            unit_price=item_request.unit_price,
            line_total=line_total,
            tax_type=item_request.tax_type,
            tax_rate=item_request.tax_rate,
            tax_amount=item_tax_amount,
            hsn_code=item_request.hsn_code,
            reference_type=item_request.reference_type,
            reference_id=item_request.reference_id,
        )
        
        invoice_item.invoice = invoice
        db.add(invoice_item)
        
        subtotal += line_total
        tax_amount += item_tax_amount

    # Update invoice totals
    invoice.subtotal = subtotal
    invoice.tax_amount = tax_amount
    invoice.total_amount = subtotal + tax_amount

    db.add(invoice)
    await db.commit()
    await db.refresh(invoice)

    # Generate PDF and send email in background
    background_tasks.add_task(generate_invoice_pdf, invoice.id)
    background_tasks.add_task(send_invoice_email, invoice.id)

    # Publish invoice event
    background_tasks.add_task(
        publish_invoice_event,
        "invoice.generated",
        {
            "invoice_id": str(invoice.id),
            "tenant_id": str(invoice.tenant_id),
            "invoice_number": invoice.invoice_number,
            "total_amount": float(invoice.total_amount),
            "due_date": invoice.due_date.isoformat(),
        },
    )

    logger.info(
        "Invoice created successfully",
        invoice_id=str(invoice.id),
        invoice_number=invoice.invoice_number,
        total_amount=invoice.total_amount,
    )

    return InvoiceResponse.model_validate(invoice)


@router.post("/monthly", response_model=List[InvoiceResponse])
async def generate_monthly_invoices(
    request: MonthlyInvoiceRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Generate monthly invoices for all active tenants"""
    
    logger.info(
        "Generating monthly invoices",
        month=request.month,
        year=request.year,
        tenant_ids_count=len(request.tenant_ids) if request.tenant_ids else 0,
    )

    generated_invoices = []

    # Get tenant IDs to process
    tenant_ids = request.tenant_ids
    if not tenant_ids:
        # TODO: Fetch all active tenants from booking service
        # For now, assume we have the list
        pass

    for tenant_id in tenant_ids or []:
        try:
            # Generate invoice for this tenant
            invoice = await generate_tenant_monthly_invoice(
                tenant_id=tenant_id,
                month=request.month,
                year=request.year,
                db=db,
                background_tasks=background_tasks,
            )
            
            if invoice:
                generated_invoices.append(invoice)

        except Exception as e:
            logger.error(
                "Failed to generate monthly invoice for tenant",
                tenant_id=str(tenant_id),
                error=str(e),
            )

    logger.info(
        "Monthly invoice generation completed",
        generated_count=len(generated_invoices),
        month=request.month,
        year=request.year,
    )

    return [InvoiceResponse.model_validate(inv) for inv in generated_invoices]


@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get invoice details"""
    
    stmt = select(Invoice).where(Invoice.id == invoice_id)
    result = await db.execute(stmt)
    invoice = result.scalar_one_or_none()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )

    return InvoiceResponse.model_validate(invoice)


@router.get("/{invoice_id}/pdf")
async def get_invoice_pdf(
    invoice_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get invoice PDF URL or generate if not exists"""
    
    stmt = select(Invoice).where(Invoice.id == invoice_id)
    result = await db.execute(stmt)
    invoice = result.scalar_one_or_none()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )

    if not invoice.pdf_url:
        # Generate PDF if not exists
        pdf_url = await generate_invoice_pdf(invoice_id)
        if pdf_url:
            invoice.pdf_url = pdf_url
            await db.commit()

    if not invoice.pdf_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate invoice PDF"
        )

    return {"pdf_url": invoice.pdf_url}


@router.post("/{invoice_id}/send")
async def send_invoice(
    invoice_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Send invoice via email"""
    
    stmt = select(Invoice).where(Invoice.id == invoice_id)
    result = await db.execute(stmt)
    invoice = result.scalar_one_or_none()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )

    # Send email in background
    background_tasks.add_task(send_invoice_email, invoice_id)

    # Update invoice status
    invoice.status = InvoiceStatus.SENT
    invoice.sent_at = datetime.utcnow()
    await db.commit()

    logger.info(
        "Invoice send queued",
        invoice_id=str(invoice_id),
        invoice_number=invoice.invoice_number,
    )

    return {"message": "Invoice send queued successfully"}


@router.get("/", response_model=InvoiceListResponse)
async def list_invoices(
    tenant_id: Optional[uuid.UUID] = None,
    status: Optional[InvoiceStatus] = None,
    invoice_type: Optional[InvoiceType] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """List invoices with filtering"""
    
    stmt = select(Invoice)
    
    if tenant_id:
        stmt = stmt.where(Invoice.tenant_id == tenant_id)
    
    if status:
        stmt = stmt.where(Invoice.status == status)
    
    if invoice_type:
        stmt = stmt.where(Invoice.invoice_type == invoice_type)
    
    if from_date:
        stmt = stmt.where(Invoice.invoice_date >= from_date)
    
    if to_date:
        stmt = stmt.where(Invoice.invoice_date <= to_date)
    
    # Get total count for pagination
    count_stmt = select(func.count()).select_from(stmt.subquery())
    count_result = await db.execute(count_stmt)
    total_count = count_result.scalar()
    
    # Apply pagination
    stmt = stmt.order_by(Invoice.created_at.desc()).offset(offset).limit(limit)
    
    result = await db.execute(stmt)
    invoices = result.scalars().all()

    return InvoiceListResponse(
        invoices=[InvoiceResponse.model_validate(inv) for inv in invoices],
        total_count=total_count,
        limit=limit,
        offset=offset,
    )


async def generate_tenant_monthly_invoice(
    tenant_id: uuid.UUID,
    month: int,
    year: int,
    db: AsyncSession,
    background_tasks: BackgroundTasks,
) -> Optional[Invoice]:
    """Generate monthly invoice for a specific tenant"""
    
    # Calculate period dates
    period_start = datetime(year, month, 1)
    if month == 12:
        period_end = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        period_end = datetime(year, month + 1, 1) - timedelta(days=1)

    # Check if invoice already exists
    existing_stmt = select(Invoice).where(
        and_(
            Invoice.tenant_id == tenant_id,
            Invoice.invoice_type == InvoiceType.COMBINED,
            Invoice.period_start == period_start,
            Invoice.period_end == period_end,
        )
    )
    result = await db.execute(existing_stmt)
    existing = result.scalar_one_or_none()
    
    if existing:
        logger.info(
            "Monthly invoice already exists",
            tenant_id=str(tenant_id),
            invoice_id=str(existing.id),
        )
        return existing

    # TODO: Fetch rent amount from booking service
    # TODO: Fetch mess charges from mess service
    # For now, create a sample invoice structure

    # Generate invoice number
    current_fy = get_current_financial_year()
    stmt = select(InvoiceSequence).where(InvoiceSequence.financial_year == current_fy)
    result = await db.execute(stmt)
    sequence = result.scalar_one_or_none()
    
    if not sequence:
        sequence = InvoiceSequence(financial_year=current_fy)
        db.add(sequence)
        await db.flush()
    
    invoice_number = sequence.generate_invoice_number()

    # Create invoice
    invoice = Invoice(
        invoice_number=invoice_number,
        tenant_id=tenant_id,
        invoice_type=InvoiceType.COMBINED,
        period_start=period_start,
        period_end=period_end,
        due_date=period_end + timedelta(days=7),  # 7 days after month end
        place_of_supply="Karnataka",
        subtotal=Decimal('0.00'),  # Will be calculated from items
        tax_amount=Decimal('0.00'),
        total_amount=Decimal('0.00'),
    )

    # Sample invoice items (in real implementation, fetch from other services)
    items = [
        {
            "description": f"Room Rent - {period_start.strftime('%B %Y')}",
            "quantity": Decimal('1.00'),
            "unit_price": Decimal('15000.00'),  # ₹15,000 rent
            "tax_type": TaxType.EXEMPT,  # Rent is usually exempt
            "tax_rate": Decimal('0.00'),
            "hsn_code": "997212",  # HSN for accommodation
        }
    ]

    subtotal = Decimal('0.00')
    tax_amount = Decimal('0.00')

    for item_data in items:
        line_total = item_data["quantity"] * item_data["unit_price"]
        item_tax = line_total * item_data["tax_rate"] / 100

        invoice_item = InvoiceItem(
            description=item_data["description"],
            quantity=item_data["quantity"],
            unit_price=item_data["unit_price"],
            line_total=line_total,
            tax_type=item_data["tax_type"],
            tax_rate=item_data["tax_rate"],
            tax_amount=item_tax,
            hsn_code=item_data["hsn_code"],
        )
        
        invoice_item.invoice = invoice
        db.add(invoice_item)
        
        subtotal += line_total
        tax_amount += item_tax

    # Update totals
    invoice.subtotal = subtotal
    invoice.tax_amount = tax_amount
    invoice.total_amount = subtotal + tax_amount

    db.add(invoice)
    await db.commit()
    await db.refresh(invoice)

    # Generate PDF and send email
    background_tasks.add_task(generate_invoice_pdf, invoice.id)
    background_tasks.add_task(send_invoice_email, invoice.id)

    # Publish event
    background_tasks.add_task(
        publish_invoice_event,
        "invoice.generated",
        {
            "invoice_id": str(invoice.id),
            "tenant_id": str(invoice.tenant_id),
            "invoice_number": invoice.invoice_number,
            "total_amount": float(invoice.total_amount),
            "due_date": invoice.due_date.isoformat(),
        },
    )

    logger.info(
        "Invoice created successfully",
        invoice_id=str(invoice.id),
        invoice_number=invoice.invoice_number,
    )

    return InvoiceResponse.model_validate(invoice)


def get_current_financial_year() -> str:
    """Get current Indian financial year (April to March)"""
    now = datetime.utcnow()
    if now.month >= 4:  # April onwards
        return f"{now.year}-{str(now.year + 1)[2:]}"
    else:  # January to March
        return f"{now.year - 1}-{str(now.year)[2:]}"