import pytest
from app.clients.supabase_client import SupabaseClient
from app.core.config import settings

supabase_client = SupabaseClient().client

@pytest.fixture(scope="session")
def supabase_auth_token():
    """
    Authenticates a test user and provides a JWT token for use in tests.
    """
    # Sign in with test credentials
    response = supabase_client.auth.sign_in_with_password(
        {"email": settings.SUPERADMIN_EMAIL, "password": settings.SUPERADMIN_PASSWORD}
    )

    # Check for successful authentication and return the access token
    if not response.session or not response.session.access_token:
        raise Exception("Authentication successful, but no access token found.")

    return response.session.access_token