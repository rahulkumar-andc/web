from django.test import SimpleTestCase, Client
from django.core.exceptions import RequestDataTooBig, TooManyFieldsSent
from django.conf import settings
import json

class DoSProtectionTest(SimpleTestCase):
    def setUp(self):
        self.client = Client()

    def test_max_number_fields(self):
        # Create a payload with more than DATA_UPLOAD_MAX_NUMBER_FIELDS
        limit = settings.DATA_UPLOAD_MAX_NUMBER_FIELDS
        data = {f'field_{i}': i for i in range(limit + 10)}
        
        # We expect a 400 Bad Request due to TooManyFieldsSent
        # Note: Django's test client might raise the exception directly depending on configuration,
        # or return 400. We'll handle both.
        try:
            response = self.client.post('/login/', data)
            self.assertEqual(response.status_code, 400)
        except TooManyFieldsSent:
            pass # Test passed

    def test_max_memory_size(self):
        # Create a payload larger than DATA_UPLOAD_MAX_MEMORY_SIZE
        limit = settings.DATA_UPLOAD_MAX_MEMORY_SIZE
        # Create a large string. 
        large_data = "a" * (limit + 1024) 
        
        try:
            # Send as form data (default content_type)
            # We put the large data in a field
            response = self.client.post(
                '/login/', 
                {'large_field': large_data}
            )
            self.assertEqual(response.status_code, 400)
        except RequestDataTooBig:
            pass # Test passed
