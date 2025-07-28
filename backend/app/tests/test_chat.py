# tests/test_chat.py
import uuid
import pytest
from fastapi import WebSocketDisconnect
from starlette.websockets import WebSocketState

CHAT_CREATE_URL = "/chat/create-chat"
WS_CHAT_PATH     = "/chat/ws/chat/"

def test_chat_with_supabase_login(customer_token, merchant_token, client):
    """
    سيناريو كامل:
    1. العميل يُنشئ محادثة مع التاجر.
    2. كلا الطرفين يتصلان بـ WebSocket المُوثَّق بالتوكن.
    3. يتبادلان رسالتين وتتحقق الاختبارات من صحّة المحتوى.
    """
    merchant_id = "8419772f-629b-417a-a8a6-e37c085ce9c2"

    # 1) إنشاء المحادثة كعميل HTTP عادي
    res = client.post(
        CHAT_CREATE_URL,
        json={"merchant_id": merchant_id},
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert res.status_code == 200
    chat_id = res.json()["id"]

    # 2) اتصال WebSocket للطرفين بتمرير التوكن كسلسلة استعلام
    ws_url_cust = f"{WS_CHAT_PATH}/{chat_id}?token={customer_token}"
    ws_url_mer  = f"{WS_CHAT_PATH}/{chat_id}?token={merchant_token}"

    with client.websocket_connect(ws_url_cust) as ws_cust, \
         client.websocket_connect(ws_url_mer)  as ws_mer:

        # العميل يرسل
        ws_cust.send_json({"content": "Hello", "image_url": None})

        # التاجر يستقبل
        msg = ws_mer.receive_json()
        assert msg["content"] == "Hello"

        # التاجر يرد
        ws_mer.send_json({"content": "Hi there!", "image_url": None})

        # العميل يستقبل
        reply = ws_cust.receive_json()
        assert reply["content"] == "Hi there!"
