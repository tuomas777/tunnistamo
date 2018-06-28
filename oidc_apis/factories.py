import factory

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
