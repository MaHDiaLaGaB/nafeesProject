# tests/test_chat_endpoints.py
import uuid
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

# adjust these imports to match your project structure:
from app.main import app
from app.services.chat_service import get_chat_service
from app.services.message_service import get_message_service
from app.dependencies.deps import CurrentUser

# --- Stub models / services ----------------------------------------------

# fixed UUIDs for consistency
TEST_CHAT_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
TEST_CUSTOMER_ID = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
TEST_MERCHANT_ID = uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
TEST_MSG_ID = uuid.UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")


class DummyChat:
    def __init__(self, id, customer_id, merchant_id):
        self.id = id
        self.customer_id = customer_id
        self.merchant_id = merchant_id


class DummyMessage:
    def __init__(self, id, conversation_id, sender_id, content, image_url=None):
        self.id = id
        self.conversation_id = conversation_id
        self.sender_id = sender_id
        self.content = content
        self.image_url = image_url


class StubChatService:
    async def create_chat(self, customer_id, merchant_id):
        return DummyChat(TEST_CHAT_ID, customer_id, merchant_id)

    async def get_chat_by_id(self, chat_id):
        if chat_id == TEST_CHAT_ID:
            return DummyChat(TEST_CHAT_ID, TEST_CUSTOMER_ID, TEST_MERCHANT_ID)
        raise HTTPException(status_code=404, detail="Chat not found")

    async def get_chats_for_customer(self, customer_id):
        return [DummyChat(TEST_CHAT_ID, customer_id, TEST_MERCHANT_ID)]

    async def get_chats_for_merchant(self, merchant_id):
        return [DummyChat(TEST_CHAT_ID, TEST_CUSTOMER_ID, merchant_id)]

    async def delete_chat(self, chat_id):
        if chat_id != TEST_CHAT_ID:
            raise HTTPException(status_code=404)
        # no-op


class StubMessageService:
    async def send_message(self, data):
        return DummyMessage(
            TEST_MSG_ID,
            data["conversation_id"],
            data["sender_id"],
            data.get("content", ""),
            data.get("image_url"),
        )

    async def get_messages_for_chat(self, conversation_id):
        # return a single message
        return [
            DummyMessage(TEST_MSG_ID, conversation_id, TEST_CUSTOMER_ID, "hello world")
        ]

    async def get_message_by_id(self, msg_id):
        if msg_id == TEST_MSG_ID:
            return DummyMessage(
                TEST_MSG_ID, TEST_CHAT_ID, TEST_CUSTOMER_ID, "hello world"
            )
        return None

    async def delete_message(self, msg_id):
        if msg_id != TEST_MSG_ID:
            raise HTTPException(status_code=404)
        # no-op


class DummyUser:
    def __init__(self, id, role):
        self.id = id
        self.role = role


# --- Fixtures & dependency overrides ------------------------------------


@pytest.fixture(autouse=True)
def override_dependencies(monkeypatch):
    # stub out ChatService & MessageService
    monkeypatch.setattr(
        get_chat_service, "__wrapped__", lambda db=None: StubChatService()
    )
    monkeypatch.setattr(
        get_message_service, "__wrapped__", lambda db=None: StubMessageService()
    )

    # stub out current user as customer
    monkeypatch.setattr(
        CurrentUser, "__call__", lambda self: DummyUser(TEST_CUSTOMER_ID, "customer")
    )

    # if you have role_required dependency factory, you can disable it:
    # e.g. monkeypatch.setattr("dependencies.auth.role_required", lambda *roles: lambda: None)

    yield


@pytest.fixture
def client():
    return TestClient(app)


# --- Tests ----------------------------------------------------------------


def test_create_chat(client, supabase_auth_token):
    payload = {
        "customer_id": str(TEST_CUSTOMER_ID),
        "merchant_id": str(TEST_MERCHANT_ID),
    }
    headers = {"Authorization": f"Bearer {supabase_auth_token}"}
    resp = client.post("/chat/create-chat", json=payload, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == str(TEST_CHAT_ID)
    assert data["customer_id"] == str(TEST_CUSTOMER_ID)
    assert data["merchant_id"] == str(TEST_MERCHANT_ID)


def test_get_chat_by_id(client, supabase_auth_token):
    headers = {"Authorization": f"Bearer {supabase_auth_token}"}
    resp = client.get(f"/chat/get/{TEST_CHAT_ID}", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == str(TEST_CHAT_ID)
    assert data["customer_id"] == str(TEST_CUSTOMER_ID)
    assert data["merchant_id"] == str(TEST_MERCHANT_ID)

    # non-existent chat
    bad_id = uuid.uuid4()
    resp = client.get(f"/chat/get/{bad_id}", headers=headers)
    assert resp.status_code == 404


def test_list_messages(client, supabase_auth_token):
    headers = {"Authorization": f"Bearer {supabase_auth_token}"}
    resp = client.get(f"/chat/get/{TEST_CHAT_ID}/messages", headers=headers)
    assert resp.status_code == 200
    msgs = resp.json()
    assert isinstance(msgs, list) and len(msgs) == 1
    m = msgs[0]
    assert m["id"] == str(TEST_MSG_ID)
    assert m["content"] == "hello world"
    assert m["conversation_id"] == str(TEST_CHAT_ID)
    assert m["sender_id"] == str(TEST_CUSTOMER_ID)


def test_websocket_echo(client, supabase_auth_token):
    headers = {"Authorization": f"Bearer {supabase_auth_token}"}
    with client.websocket_connect(f"/chat/ws/{TEST_CHAT_ID}", headers=headers) as ws:
        # send a chat message
        ws.send_json({"content": "ping", "image_url": None})

        # receive broadcast
        msg = ws.receive_json(timeout=1.0)
        assert msg["content"] == "ping"
        assert msg["conversation_id"] == str(TEST_CHAT_ID)
        assert msg["sender_id"] == str(TEST_CUSTOMER_ID)
