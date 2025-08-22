# tests/conftest.py
import os
import pytest
from fastapi.testclient import TestClient
from jose import jwt

from app.main import app
from app.clients.supabase_client import SupabaseClient

# -----------------------------------------------------------------------------
# ثوابت بيانات الاختبار
# -----------------------------------------------------------------------------
CUSTOMER_EMAIL  = os.getenv("TEST_CUSTOMER_EMAIL",  "user@user.com")
MERCHANT_EMAIL  = os.getenv("TEST_MERCHANT_EMAIL",  "merchant@merchant.com")
TEST_PASSWORD   = os.getenv("TEST_PASSWORD",        "Password1!")

# -----------------------------------------------------------------------------
# عملاء عامّة
# -----------------------------------------------------------------------------
@pytest.fixture(scope="session")
def supabase_client():
    """عميل Supabase واحد طيلة جلسة الاختبار."""
    return SupabaseClient().client


@pytest.fixture(scope="session")
def client():
    """TestClient واحد طيلة الجلسة لتجنّب إعادة الإقلاع المستمر."""
    return TestClient(app)


# -----------------------------------------------------------------------------
# توكنات المستخدمين
# -----------------------------------------------------------------------------
def _signin_or_skip(client, email):
    resp = client.auth.sign_in_with_password({"email": email, "password": TEST_PASSWORD})
    if not resp.session or not resp.session.access_token:
        pytest.skip(f"⚠️  لا يمكن تسجيل الدخول لحساب الاختبار {email}")
    return resp.session.access_token


@pytest.fixture(scope="session")
def customer_token(supabase_client):
    return _signin_or_skip(supabase_client, CUSTOMER_EMAIL)


@pytest.fixture(scope="session")
def merchant_token(supabase_client):
    return _signin_or_skip(supabase_client, MERCHANT_EMAIL)

# -----------------------------------------------------------------------------
# رؤوس المصادقة الجاهزة
# -----------------------------------------------------------------------------
@pytest.fixture
def customer_auth_headers(customer_token):
    return {"Authorization": f"Bearer {customer_token}"}


@pytest.fixture
def merchant_auth_headers(merchant_token):
    return {"Authorization": f"Bearer {merchant_token}"}

# -----------------------------------------------------------------------------
# استخراج user_id من التوكن
# -----------------------------------------------------------------------------
def _extract_user_id(token: str) -> str:
    claims = jwt.get_unverified_claims(token)
    sub    = claims.get("sub")
    if not sub:
        raise ValueError("JWT has no 'sub' claim")
    return sub


@pytest.fixture(scope="session")
def customer_id(customer_token):
    return _extract_user_id(customer_token)


@pytest.fixture(scope="session")
def merchant_id(merchant_token):
    return _extract_user_id(merchant_token)


@pytest.fixture(scope="session")
def customer_client(customer_token):
    """A TestClient that will act as the customer."""
    client = TestClient(app)
    # you can pre-inject the header if you like:
    client.headers.update({"Authorization": f"Bearer {customer_token}"})
    return client

@pytest.fixture(scope="session")
def merchant_client(merchant_token):
    """A TestClient that will act as the merchant."""
    client = TestClient(app)
    client.headers.update({"Authorization": f"Bearer {merchant_token}"})
    return client
