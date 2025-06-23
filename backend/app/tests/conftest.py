import pytest
from app.clients.supabase_client import SupabaseClient
from app.core.config import settings
# from httpx import AsyncClient
from fastapi.testclient import TestClient
from app.main import app
# from app.database import get_session, Base, engine
# from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt

supabase_client = SupabaseClient().client

@pytest.fixture
def client():
    return TestClient(app)


# @pytest.fixture(scope="session")
# def supabase_auth_token():
#     """
#     Authenticates a test user and provides a JWT token for use in tests.
#     """
#     # Sign in with test credentials
#     response = supabase_client.auth.sign_in_with_password(
#         {"email": settings.SUPERADMIN_EMAIL, "password": settings.SUPERADMIN_PASSWORD}
#     )

#     # Check for successful authentication and return the access token
#     if not response.session or not response.session.access_token:
#         raise Exception("Authentication successful, but no access token found.")

#     return response.session.access_token


@pytest.fixture(scope="session")
def customer_token():
    response = supabase_client.auth.sign_in_with_password(
        {
            "email": "user@user.com",
            "password": "Password1!",
        }
    )
    
    if not response.session or not response.session.access_token:
        raise Exception("Customer login failed or token missing.")
    return response.session.access_token

@pytest.fixture(scope="session")
def merchant_token():
    response = supabase_client.auth.sign_in_with_password(
        {
            "email": "merchant@merchant.com",
            "password": "Password1!",
        }
    )
    if not response.session or not response.session.access_token:
        raise Exception("Merchant login failed or token missing.")
    return response.session.access_token

@pytest.fixture
def customer_auth_headers(customer_token):
    return {"Authorization": f"Bearer {customer_token}"}

@pytest.fixture
def merchant_auth_headers(merchant_token):
    return {"Authorization": f"Bearer {merchant_token}"}


def extract_user_id(token: str) -> str:
    # pull out claims without any key or signature check
    claims = jwt.get_unverified_claims(token)
    return claims["sub"]

@pytest.fixture
def customer_id(customer_token):
    return extract_user_id(customer_token)

@pytest.fixture
def merchant_id(merchant_token):
    return extract_user_id(merchant_token)

