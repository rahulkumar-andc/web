import factory
from django.contrib.auth import get_user_model
from core.models import Service, Note, OTP
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.Sequence(lambda n: f'user{n}@example.com')
    password = factory.PostGenerationMethodCall('set_password', 'password123')
    is_active = True

class ServiceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Service

    title = factory.Sequence(lambda n: f'Service {n}')
    description = "Test Description"
    icon = "fas fa-code"

class NoteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Note

    title = factory.Sequence(lambda n: f'Note {n}')
    description = "Test Note Description"
    author = factory.SubFactory(UserFactory)
    file = factory.django.FileField(filename='test.pdf')

class OTPFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = OTP

    user = factory.SubFactory(UserFactory)
    otp_code = '123456'
    expires_at = factory.LazyFunction(lambda: timezone.now() + timedelta(minutes=10))
