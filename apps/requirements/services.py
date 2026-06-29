import csv
import io
import logging

from django.conf import settings
from django.core.mail import EmailMessage

logger = logging.getLogger(__name__)


def send_form_backup_email(header):
    if not settings.FORM_BACKUP_EMAIL:
        return
    try:
        items = list(header.lines.select_related("item").all())
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(["Form No.", "Order ID", "Date", "Volunteer", "Route", "Upashray", "Items"])
        summary = "; ".join(f"{li.item.item_name}({li.required_qty})" for li in items if li.required_qty)
        w.writerow([
            header.form_number or "",
            header.order_number or "",
            header.requirement_date,
            header.volunteer_name,
            header.get_route_area_display(),
            str(header.upashray),
            summary,
        ])
        email = EmailMessage(
            subject=f"[Form Backup] {header.form_number or header.order_number or 'New Form'}",
            body=f"Form confirmed.\n\nForm No: {header.form_number or '-'}\nOrder ID: {header.order_number or '-'}\nDate: {header.requirement_date}\nVolunteer: {header.volunteer_name}\nRoute: {header.get_route_area_display()}\nUpashray: {header.upashray}\n\nItems:\n{summary}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[settings.FORM_BACKUP_EMAIL],
        )
        email.attach("form_backup.csv", buf.getvalue(), "text/csv")
        email.send()
    except Exception as e:
        logger.error("Failed to send form backup email: %s", e)