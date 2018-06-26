from __future__ import unicode_literals

import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _
from helusers.models import AbstractUser
from oauth2_provider.models import AbstractApplication
from oidc_provider.models import Client


class User(AbstractUser):
    primary_sid = models.CharField(max_length=100, unique=True)

    def save(self, *args, **kwargs):
        if not self.primary_sid:
            self.primary_sid = uuid.uuid4()
        return super(User, self).save(*args, **kwargs)


def get_provider_ids():
    from django.conf import settings
    from social_core.backends.utils import load_backends
    return [(name, name) for name in load_backends(settings.AUTHENTICATION_BACKENDS).keys()]


@python_2_unicode_compatible
class LoginMethod(models.Model):
    provider_id = models.CharField(
        max_length=50, unique=True,
        choices=sorted(get_provider_ids()))
    name = models.CharField(max_length=100)
    background_color = models.CharField(max_length=50, null=True, blank=True)
    logo_url = models.URLField(null=True, blank=True)
    short_description = models.TextField(null=True, blank=True)
    order = models.PositiveIntegerField(null=True)

    def __str__(self):
        return "{} ({})".format(self.name, self.provider_id)

    class Meta:
        ordering = ('order',)


class OptionsBase(models.Model):
    SITE_TYPES = (
        ('dev', 'Development'),
        ('test', 'Testing'),
        ('production', 'Production')
    )
    site_type = models.CharField(max_length=20, choices=SITE_TYPES, null=True,
                                 verbose_name='Site type')
    login_methods = models.ManyToManyField(LoginMethod)
    include_ad_groups = models.BooleanField(default=False)

    class Meta:
        abstract = True


class Application(OptionsBase, AbstractApplication):
    class Meta:
        ordering = ('site_type', 'name')


class OidcClientOptions(OptionsBase):
    oidc_client = models.OneToOneField(Client, related_name='+', on_delete=models.CASCADE,
                                       verbose_name=_("OIDC Client"))

    def __str__(self):
        return 'Options for OIDC Client "{}"'.format(self.oidc_client.name)

    class Meta:
        verbose_name = _("OIDC Client Options")
        verbose_name_plural = _("OIDC Client Options")


class UserLoginEntryManager(models.Manager):
    def create_from_request(self, request, **kwargs):
        kwargs.setdefault('user', request.user)
        kwargs.setdefault('timestamp', now())
        return self.create(**kwargs)


class UserLoginEntry(models.Model):
    user = models.ForeignKey(User, verbose_name=_('user'), related_name='login_entries', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(verbose_name=_('timestamp'))

    target_app = models.ForeignKey(
        Application, verbose_name='target app', related_name='user_login_entries_as_target', null=True, blank=True,
        on_delete=models.PROTECT
    )
    requesting_app = models.ForeignKey(
        Application, verbose_name='requesting app', related_name='user_login_entries_as_requester', null=True,
        blank=True, on_delete=models.PROTECT
    )

    target_client = models.ForeignKey(
        Client, verbose_name='target client', related_name='user_login_entries_as_target', null=True, blank=True,
        on_delete=models.PROTECT
    )
    requesting_client = models.ForeignKey(
        Client, verbose_name='requesting client', related_name='user_login_entries_as_requester', null=True,
        blank=True, on_delete=models.PROTECT
    )

    ip_address = models.CharField(verbose_name=_('IP address'), max_length=50)
    geo_location = models.CharField(verbose_name=_('geo location'), max_length=100, null=True, blank=True)

    objects = UserLoginEntryManager()

    class Meta:
        verbose_name = _('user login entry')
        verbose_name_plural = _('user login entries')
        ordering = ('id',)

    def clean(self):
        if (self.target_app or self.requesting_app) and (self.target_client or self.requesting_client):
            raise ValidationError('Cannot set both apps and clients.')
        if not (self.target_app and self.requesting_app) and not (self.target_client and self.requesting_client):
            raise ValidationError('Either apps or clients must be set.')

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
