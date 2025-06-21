# tests/test_users_endpoints.py
import uuid
import pytest
from fastapi.testclient import TestClient
from fastapi import status, HTTPException

# adjust these imports to your project structure
from app.main import app
from app.services.users_service import get_user_service
from app.dependencies.deps import CurrentUser
from app.schemas.users import UserOut, UserBase, UserUpdate, UserRole

# mount the router if not already (only needed if app.main doesn't include it)
# app.include_router(users_router, prefix="/users")

# -- test constants --------------------------------------------------------

TEST_USER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
TEST_OTHER_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")
TEST_EMAIL = "alice@example.com"
TEST_FULL_NAME = "Alice Liddell"
TEST_ROLE = "customer"
TEST_NEW_NAME = "Alice Wonderland"

# -- stub service ----------------------------------------------------------


class StubUserService:
    async def create_user(self, user_data: dict):
        # echo back with a fixed ID
        return {"id": str(TEST_USER_ID), **user_data}

    async def get_all_users(self, skip: int = 0, limit: int = 100):
        return [
            {
                "id": str(TEST_USER_ID),
                **{
                    "email": TEST_EMAIL,
                    "full_name": TEST_FULL_NAME,
                    "role": TEST_ROLE,
                },
            },
            {
                "id": str(TEST_OTHER_ID),
                **{
                    "email": "bob@example.com",
                    "full_name": "Bob Builder",
                    "role": "merchant",
                },
            },
        ]

    async def get_user_by_id(self, user_id: uuid.UUID):
        if user_id == TEST_USER_ID:
            return {
                "id": str(TEST_USER_ID),
                "email": TEST_EMAIL,
                "full_name": TEST_FULL_NAME,
                "role": TEST_ROLE,
            }
        raise HTTPException(status_code=404, detail="User not found")

    async def update_user(self, user_id: uuid.UUID, data: dict, current_user):
        if user_id != TEST_USER_ID:
            raise HTTPException(status_code=404)
        return {"id": str(TEST_USER_ID), **data}

    async def delete_user(self, user_id: uuid.UUID, current_user):
        if user_id != TEST_USER_ID:
            raise HTTPException(status_code=404)
        # no-op


# -- fixture to override dependencies --------------------------------------


@pytest.fixture(autouse=True)
def override_user_deps(monkeypatch):
    # a dummy current user (as if already authenticated)
    dummy_current = UserOut(
        id=TEST_USER_ID,
        email=TEST_EMAIL,
        full_name=TEST_FULL_NAME,
        role=UserRole.customer,
    )
    # stub out get_user_service → our StubUserService
    monkeypatch.setattr(
        get_user_service, "__wrapped__", lambda db=None: StubUserService()
    )
    # stub out CurrentUser → always return our dummy_current
    monkeypatch.setattr(CurrentUser, "__call__", lambda self: dummy_current)

    yield


@pytest.fixture
def client():
    return TestClient(app)


# -- tests -----------------------------------------------------------------


def test_create_user(client, supabase_auth_token):
    payload = {
        "email": TEST_EMAIL,
        "full_name": TEST_FULL_NAME,
        "password": "secret123",
        "role": TEST_ROLE,
    }
    headers = {"Authorization": f"Bearer {supabase_auth_token}"}
    resp = client.post("/users/create", json=payload, headers=headers)
    assert resp.status_code == status.HTTP_201_CREATED
    data = resp.json()
    assert data["id"] == str(TEST_USER_ID)
    assert data["email"] == TEST_EMAIL
    assert data["full_name"] == TEST_FULL_NAME
    assert data["role"] == TEST_ROLE


def test_read_current_user(client, supabase_auth_token):
    headers = {"Authorization": f"Bearer {supabase_auth_token}"}
    resp = client.get("/users/me", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == str(TEST_USER_ID)
    assert data["email"] == TEST_EMAIL


def test_list_users(client, supabase_auth_token):
    headers = {"Authorization": f"Bearer {supabase_auth_token}"}
    resp = client.get("/users/getAll?skip=0&limit=10", headers=headers)
    assert resp.status_code == 200
    users = resp.json()
    assert isinstance(users, list) and len(users) == 2
    ids = {u["id"] for u in users}
    assert str(TEST_USER_ID) in ids and str(TEST_OTHER_ID) in ids


def test_read_user_by_id(client, supabase_auth_token):
    headers = {"Authorization": f"Bearer {supabase_auth_token}"}
    resp = client.get(f"/users/get/{TEST_USER_ID}", headers=headers)
    assert resp.status_code == 200
    u = resp.json()
    assert u["id"] == str(TEST_USER_ID)
    # non‐existent
    bad = client.get(f"/users/get/{uuid.uuid4()}", headers=headers)
    assert bad.status_code == 404


def test_update_user(client, supabase_auth_token):
    update_payload = {"full_name": TEST_NEW_NAME}
    headers = {"Authorization": f"Bearer {supabase_auth_token}"}
    resp = client.put(
        f"/users/update/{TEST_USER_ID}", json=update_payload, headers=headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == str(TEST_USER_ID)
    assert data["full_name"] == TEST_NEW_NAME

    # updating someone else → 404
    bad = client.put(
        f"/users/update/{uuid.uuid4()}", json=update_payload, headers=headers
    )
    assert bad.status_code == 404


def test_delete_user(client, supabase_auth_token):
    # successful delete
    headers = {"Authorization": f"Bearer {supabase_auth_token}"}
    resp = client.delete(f"/users/delete/{TEST_USER_ID}", headers=headers)
    assert resp.status_code == status.HTTP_204_NO_CONTENT

    # deleting non‐existent
    resp2 = client.delete(f"/users/delete/{uuid.uuid4()}", headers=headers)
    assert resp2.status_code == 404
