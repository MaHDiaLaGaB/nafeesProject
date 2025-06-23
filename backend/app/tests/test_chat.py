# tests/test_chat.py
import uuid
import pytest
from fastapi import WebSocketDisconnect
from starlette.websockets import WebSocketState

CHAT_CREATE_URL = "/chat/create-chat"
WS_CHAT_URL     = "/chat/ws"

def test_chat_with_supabase_login(
    client,
    customer_auth_headers,
    merchant_auth_headers,
):
    customer_id = "69ece0df-2946-4d0f-b1c5-c2546471b9a0"
    merchant_id = "8419772f-629b-417a-a8a6-e37c085ce9c2"

    # create the chat as the customer
    res = client.post(
        CHAT_CREATE_URL,
        headers=customer_auth_headers,
        json={"merchant_id": merchant_id},
    )
    assert res.status_code == 200
    chat_id = res.json()["id"]

    # connect both sides synchronously
    with client.websocket_connect(f"{WS_CHAT_URL}/{chat_id}", headers=customer_auth_headers) as ws1:
        with client.websocket_connect(f"{WS_CHAT_URL}/{chat_id}", headers=merchant_auth_headers) as ws2:
            # customer sends
            ws1.send_json({"content": "Hello", "image_url": None})
            # merchant receives
            msg = ws2.receive_json()
            assert msg["content"] == "Hello"

            # merchant replies
            ws2.send_json({"content": "Hi there!", "image_url": None})
            # customer receives
            reply = ws1.receive_json()
            assert reply["content"] == "Hi there!"
