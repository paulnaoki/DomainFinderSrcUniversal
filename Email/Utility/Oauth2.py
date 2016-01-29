import urllib.parse
from oauth2client.client import OAuth2Credentials
__author__ = 'paulnaoki'


class CustomOAuth2Credentials(OAuth2Credentials):

    def _generate_refresh_request_body(self):
        """Generate the body that will be used in the refresh request."""
        body = urllib.parse.urlencode({
            'grant_type': 'refresh_token',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'refresh_token': self.refresh_token,
            'scope': ','.join(list(self.scopes)),
        })
        return body
