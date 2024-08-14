# your_app/management/commands/run_function.py

import time

import schedule
from django.core.management.base import BaseCommand

from helpers.functions import clean_older_technician_bookings


class Command(BaseCommand):
    help = 'Run a functions at regular intervals'

    def handle(self, *args, **options):
        schedule.every(1).seconds.do(clean_older_technician_bookings)

        while True:
            schedule.run_pending()
            time.sleep(1)
