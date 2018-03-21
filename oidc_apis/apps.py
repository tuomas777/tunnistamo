from django.apps import AppConfig


class OidcApisConfig(AppConfig):
    name = 'oidc_apis'

    def ready(self):
        from oidc_apis.models import AutoConsentScope
        from oidc_provider.views import AuthorizeEndpoint

        _get_scopes_information = AuthorizeEndpoint.get_scopes_information

        def get_scopes_information(self):
            scopes_list = _get_scopes_information(self)
            auto_consent_scopes = set(
                AutoConsentScope.objects.filter(client=self.client).values_list('scope', flat=True)
            )
            filtered_scope_list = [scope for scope in scopes_list if scope['scope'] not in auto_consent_scopes]
            return filtered_scope_list

        AuthorizeEndpoint.get_scopes_information = get_scopes_information
