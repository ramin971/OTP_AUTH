# wait_for_db.py بهبودیافته
import time
import socket
from django.core.management.base import BaseCommand
from django.db import connections
from django.db.utils import OperationalError

class Command(BaseCommand):
    def handle(self, *args, **options):
        self.stdout.write('####### Waiting for database...')
        
        # ابتدا بررسی پورت
#        db_host = connections['default'].settings_dict['HOST']
#        db_port = connections['default'].settings_dict['PORT']
        
        while True:
            try:                
                # 2. بررسی اتصال واقعی به دیتابیس
                db_conn = connections['default']
                db_conn.cursor()
                break
                
            except OperationalError:
                self.stdout.write('****NOK***** Database unavailable, waiting...')
                time.sleep(1)
        
        self.stdout.write(self.style.SUCCESS('####OK#### Database is available!'))
