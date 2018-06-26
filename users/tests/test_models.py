import pytest
from django.core.exceptions import ValidationError
from django.utils.crypto import get_random_string
from oidc_provider.tests.app.utils import create_fake_client

from users.factories import ApplicationFactory, UserLoginEntryFactory
from users.models import User


@pytest.mark.django_db
def test_user_primary_sid(user_factory):
    user = User.objects.create(
        username=get_random_string,
        email='{}@example.com'.format(get_random_string)
    )

    assert user.primary_sid is not None


@pytest.mark.parametrize('fields, expected_error', [
    ({}, 'Either apps or clients must be set.'),
    ({'target_app'}, 'Either apps or clients must be set.'),
    ({'target_client'}, 'Either apps or clients must be set.'),
    ({'target_app', 'target_client'}, 'Cannot set both apps and clients.'),
    ({'target_app', 'requesting_app', 'target_client'}, 'Cannot set both apps and clients.'),
    ({'target_app', 'requesting_app', 'target_client', 'requesting_app'}, 'Cannot set both apps and clients.'),
    ({'target_app', 'requesting_app'}, None),
    ({'target_client', 'requesting_client'}, None),

])
@pytest.mark.django_db
def test_user_login_entry_constraints(fields, expected_error):
    app1, app2 = ApplicationFactory.create_batch(2)
    client1 = create_fake_client('code')
    client2 = create_fake_client('code')
    all_attrs = {
        'target_app': app1,
        'requesting_app': app2,
        'target_client': client1,
        'requesting_client': client2,
    }
    attrs = {k: v for k, v in all_attrs.items() if k in fields}

    if expected_error:
        with pytest.raises(ValidationError) as e:
            UserLoginEntryFactory(**attrs)
        assert expected_error in str(e)
    else:
        UserLoginEntryFactory(**attrs)
