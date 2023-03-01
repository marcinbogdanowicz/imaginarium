import time
from django.db import connections
from django.db.utils import OperationalError
from django.core.management import BaseCommand


class Command(BaseCommand):
    """
    Pauses execution to wait for database.
    """

    def handle(self, *args, **kwars):
        self.stdout.write('Waiting for database...')
        db_connection = None
        while not db_connection:
            try:
                db_connection = connections['default']
            except OperationalError:
                time.sleep(0.3)
        
        self.stdout.write('Database available.')