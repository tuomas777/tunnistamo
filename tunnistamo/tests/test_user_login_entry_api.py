import pytest
from django.utils.dateparse import parse_datetime
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from tunnistamo.factories import UserFactory
from users.factories import ApplicationFactory, UserLoginEntryFactory

URL = reverse('v1:userloginentry-list')


@pytest.fixture
def user_api_client():
    user = UserFactory()
    api_client = APIClient()
    api_client.force_authenticate(user)
    api_client.user = user
    return api_client


def test_user_login_entry_endpoint_needs_authenticated_user():
    api_client = APIClient()
    resp = api_client.get(URL)
    assert resp.status_code == 403


@pytest.mark.django_db
def test_user_login_entry_endpoint_disallowed_methods(user_api_client):
    for method in ('post', 'put', 'patch', 'delete'):
        resp = getattr(user_api_client, method)(URL)
        assert resp.status_code == 405


@pytest.mark.django_db
def test_user_login_entry_endpoint_success(user_api_client):
    user = user_api_client.user

    target_app, requesting_app = ApplicationFactory.create_batch(2)

    entry_1 = UserLoginEntryFactory(user=user)
    entry_2 = UserLoginEntryFactory(user=user, target_client=None, requesting_client=None,  # noqa
                                    target_app=target_app, requesting_app=requesting_app)

    resp = user_api_client.get(URL)
    assert resp.status_code == 200

    results = resp.data['results']
    assert len(results) == 2

    entry_data_1 = results[0]
    assert set(entry_data_1.keys()) == {'timestamp', 'target', 'ip_address', 'geo_location'}
    assert parse_datetime(entry_data_1['timestamp']) == entry_1.timestamp
    assert entry_data_1['target'] == entry_1.target_client.name
    assert entry_data_1['ip_address'] == entry_1.ip_address

    entry_data_2 = results[1]
    assert entry_data_2['target'] == target_app.name


@pytest.mark.django_db
def test_user_login_entry_endpoint_cannot_see_others_entries(user_api_client):
    other_user = UserFactory()

    UserLoginEntryFactory(user=user_api_client.user, ip_address='1.2.3.4')
    UserLoginEntryFactory(user=other_user, ip_address='9.8.7.6')

    resp = user_api_client.get(URL)
    assert resp.status_code == 200
    results = resp.data['results']
    assert len(results) == 1
    assert results[0]['ip_address'] == '1.2.3.4'
