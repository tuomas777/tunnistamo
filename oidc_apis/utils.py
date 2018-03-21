from collections import OrderedDict
from datetime import timedelta

from django.utils import timezone
from oidc_provider import settings
from oidc_provider.models import UserConsent

from .models import AutoConsentScope


def combine_uniquely(iterable1, iterable2):
    """
    Combine unique items of two sequences preserving order.

    :type seq1: Iterable[Any]
    :type seq2: Iterable[Any]
    :rtype: list[Any]
    """
    result = OrderedDict.fromkeys(iterable1)
    for item in iterable2:
        result[item] = None
    return list(result.keys())


def after_userlogin_hook(request, user, client):
    """Marks Django session modified

    The purpose of this function is to keep the session used by the
    oidc-provider fresh. This is achieved by pointing
    'OIDC_AFTER_USERLOGIN_HOOK' setting to this."""
    request.session.modified = True

    create_auto_consent_scopes(user, client)

    # Return None to continue the login flow
    return None


def create_auto_consent_scopes(user, client):
    date_given = timezone.now()
    expires_at = date_given + timedelta(
        days=settings.get('OIDC_SKIP_CONSENT_EXPIRE'))

    uc, created = UserConsent.objects.get_or_create(
        user=user,
        client=client,
        defaults={
            'expires_at': expires_at,
            'date_given': date_given,
        }
    )

    auto_scopes = AutoConsentScope.objects.filter(client=client).values_list('scope', flat=True)

    if created:
        uc.scope = ['openid'] + list(auto_scopes)
    else:
        for auto_scope in auto_scopes:
            if auto_scope not in uc.scope:
                uc.scope += [auto_scope]

    # Rewrite expires_at and date_given if object already exists.
    if not created:
        uc.expires_at = expires_at
        uc.date_given = date_given

    uc.save()
