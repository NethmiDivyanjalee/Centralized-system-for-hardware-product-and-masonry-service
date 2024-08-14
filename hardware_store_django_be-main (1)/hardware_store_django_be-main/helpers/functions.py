from datetime import datetime

import decimal
from datetime import timedelta

import pytz
from django.utils import timezone

from marketplace.models import TechnicianBooking


def clean_older_technician_bookings():
    expired_bookings = TechnicianBooking.objects.filter(created_time__lt=timezone.now()-timedelta(days=1))
    for exp_booking in expired_bookings:
        exp_booking.delete()
        print(f"Expired booking request: {exp_booking} removed.")


def process_payment(amount: decimal) -> bool:
    """Process the payment and returns True if success. Else False"""

    # test implementation
    return True
    pass
