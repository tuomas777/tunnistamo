import datetime
import json

import pytest
import pytz
from Cryptodome.PublicKey import RSA
from django.urls import reverse
from django.utils.timezone import now
from oidc_provider.lib.utils.token import decode_id_token
from oidc_provider.models import RSAKey
from oidc_provider.tests.app.utils import create_fake_client, create_fake_token

from oidc_apis.factories import ApiScopeFactory
from oidc_apis.views import get_api_tokens_view
from tunnistamo.factories import UserFactory
from users.models import UserLoginEntry


@pytest.fixture(autouse=True)
def rsa_key():
    key = RSA.generate(1024)
    rsakey = RSAKey(key=key.exportKey('PEM').decode('utf8'))
    rsakey.save()
    return rsakey


@pytest.mark.django_db
def test_get_api_tokens_view_generates_user_login_entry(rf):
    request = rf.get(reverse(get_api_tokens_view), REMOTE_ADDR='1.2.3.4')
    user = UserFactory()
    request.user = user

    client = create_fake_client('code')
    api_scope = ApiScopeFactory()
    api_scope.allowed_apps.add(client)
    api = api_scope.api
    token = create_fake_token(user, ['openid', api.identifier], client)

    resp = get_api_tokens_view(request, token=token)
    assert resp.status_code == 200

    assert UserLoginEntry.objects.count() == 1
    entry = UserLoginEntry.objects.first()
    assert entry.user == user
    assert entry.requesting_client == client
    assert entry.target_client == api.oidc_client
    assert (now() - entry.timestamp) < datetime.timedelta(minutes=1)
    assert entry.ip_address == '1.2.3.4'

    data = json.loads(resp.content)
    api_token = data[api.identifier]
    decoded_token = decode_id_token(api_token, client)
    assert entry.timestamp == datetime.datetime.fromtimestamp(decoded_token['iat'], tz=pytz.utc)
