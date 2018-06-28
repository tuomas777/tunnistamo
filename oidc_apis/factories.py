import factory
from oidc_provider.models import Client

from .models import Api, ApiDomain, ApiScope


class ApiDomainFactory(factory.django.DjangoModelFactory):
    identifier = factory.Faker('url')

    class Meta:
        model = ApiDomain


class ApiFactory(factory.django.DjangoModelFactory):
    domain = factory.SubFactory(ApiDomainFactory)
    name = factory.Faker('first_name')

    class Meta:
        model = Api


class ApiScopeFactory(factory.django.DjangoModelFactory):
    api = factory.SubFactory(ApiFactory)

    class Meta:
        model = ApiScope

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """
        Call `full_clean` before saving to get possible missing identifier autopopulated.
        """
        obj = model_class(*args, **kwargs)
        obj.full_clean()
        obj.save()
        return obj


class ClientFactory(factory.django.DjangoModelFactory):
    name = factory.Sequence(lambda n: 'test_client_{}'.format(n))
    client_id = factory.Faker('uuid4')
    client_secret = factory.Faker('ean13')
    response_type = 'code'
    redirect_uris = ['http://example.com/']
    require_consent = True

    class Meta:
        model = Client
