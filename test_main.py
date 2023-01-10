from fastapi.testclient import TestClient
import pytest
import re

from main import app

client = TestClient(app)


def test_read_main():
    response = client.get("/")
    assert response.status_code == 200


@pytest.fixture
def send_json_message():
    return {'text': 'тестовый текст', 'date': '10-01-2023'}


@pytest.fixture(params=[x for x in range(1, 5)])
def expected_json_message(request):
    return {'text': 'тестовый текст', 'date': '10-01-2023', 'message_count': request.param}


@pytest.fixture(scope="module")
def client_websocket_connection():
    response = client.get("/")
    html_str = response.text
    client_cookie_string_match = re.search(r'const client_cookie_string = \'(.+)\';$', html_str, re.MULTILINE)
    client_cookie_string = client_cookie_string_match.group(1)
    with client.websocket_connect("/ws/" + client_cookie_string) as websocket:
        yield websocket


def test_websocket(client_websocket_connection, send_json_message, expected_json_message):
    client_websocket_connection.send_json(send_json_message)
    data = client_websocket_connection.receive_json()
    assert data == expected_json_message
