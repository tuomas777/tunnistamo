import datetime

import pytest
import pytz
from django.utils.timezone import now
from oauth2_provider.models import get_access_token_model
from rest_framework.test import APIClient

from hkijwt.models import AppToAppPermission
from users.factories import ApplicationFactory, UserFactory
from users.models import UserLoginEntry


@pytest.mark.django_db
def test_get_jwt_view_generates_user_login_entry():
    user = UserFactory()
    target_app, requester_app = ApplicationFactory.create_batch(2)
    AppToAppPermission.objects.create(requester=requester_app, target=target_app)

    access_token = get_access_token_model().objects.create(
        user=user, expires=datetime.datetime(year=2100, month=1, day=1, tzinfo=pytz.UTC), application=requester_app,
        token='123', scope='read'
    )

    api_client = APIClient()
    resp = api_client.get(
        '/jwt-token/?target_app={}'.format(target_app.client_id), REMOTE_ADDR='1.2.3.4',
        HTTP_AUTHORIZATION='Bearer {}'.format(access_token.token)
    )
    assert resp.status_code == 200

    assert UserLoginEntry.objects.count() == 1
    entry = UserLoginEntry.objects.first()
    assert entry.user == user
    assert entry.target_app == target_app
    assert entry.requesting_app == requester_app
    assert (now() - entry.timestamp) < datetime.timedelta(minutes=1)
    assert entry.ip_address == '1.2.3.4'
