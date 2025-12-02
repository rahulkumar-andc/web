import os
import django
from django.test import RequestFactory

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'villen.settings')
django.setup()

from core.models import CustomUser
from core.middleware import WAFMiddleware

def verify_reputation():
    print("Verifying Reputation System...")
    
    # 1. Create/Get User
    user, created = CustomUser.objects.get_or_create(username='reputation_test_user')
    user.reputation_score = 100
    user.save()
    print(f"Initial Score: {user.reputation_score}")
    
    # 2. Simulate Penalty
    print("\nTest 1: Penalty Application...")
    user.reputation_score -= 5
    user.save()
    print(f"New Score: {user.reputation_score}")
    if user.reputation_score == 95:
        print("Score Decreased -> PASS")
    else:
        print("Score Update Failed -> FAIL")
        
    # 3. Simulate Blocking
    print("\nTest 2: Blocking Logic...")
    user.reputation_score = -10
    user.save()
    
    factory = RequestFactory()
    request = factory.get('/')
    request.user = user
    
    middleware = WAFMiddleware(lambda r: None)
    response = middleware._check_reputation(request)
    
    if response and response.status_code == 403:
        print("Blocked User (403) -> PASS")
    else:
        print("Failed to Block User -> FAIL")

if __name__ == '__main__':
    verify_reputation()
