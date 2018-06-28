import factory
from django.utils.timezone import now

from oidc_apis.factories import ClientFactory
from tunnistamo.factories import UserFactory
from users.models import Application, UserLoginEntry


class ApplicationFactory(factory.django.DjangoModelFactory):
    name = factory.Sequence(lambda n: 'test_app_{}'.format(n))
    redirect_uris = "http://localhost http://example.com",
    user = factory.SubFactory(UserFactory)
    client_type = Application.CLIENT_CONFIDENTIAL,
    authorization_grant_type = Application.GRANT_AUTHORIZATION_CODE,

    class Meta:
        model = Application


class UserLoginEntryFactory(factory.django.DjangoModelFactory):
    user = factory.SubFactory(UserFactory)
    timestamp = factory.LazyFunction(now)
    ip_address = factory.Faker('ipv4')
    target_client = factory.SubFactory(ClientFactory)
    requesting_client = factory.SubFactory(ClientFactory)

    class Meta:
        model = UserLoginEntry
