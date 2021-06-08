import os
import requests
import re

SERVER_IP = os.getenv("SERVER_IP")
SERVER_PORT = os.getenv("SERVER_PORT")
BASE_URL = f"http://{SERVER_IP}:{SERVER_PORT}/babytracker"


def test_is_up():
    resp = requests.post(BASE_URL)
    assert resp.status_code == 200
    print(resp.text)


def test_create_list_delete_feed_record():
    params = {"text": "12:30 12:35"}
    resp = requests.post(BASE_URL + "/feed", data=params)
    assert resp.status_code == 200
    print(resp.json())
    assert "error" not in resp.json()["text"]

    params = {"text": "list"}
    resp = requests.post(BASE_URL + "/feed", data=params)
    assert resp.status_code == 200
    print(resp.json())
    assert "error" not in resp.json()["text"]
    assert "12:30" in resp.json()["text"]
    assert "00:05" in resp.json()["text"]

    params = {"text": "analyze total"}
    resp = requests.post(BASE_URL + "/feed", data=params)
    assert resp.status_code == 200
    print(resp.json())
    assert "error" not in resp.json()["text"]

    params = {"text": "analyze avg"}
    resp = requests.post(BASE_URL + "/feed", data=params)
    assert resp.status_code == 200
    print(resp.json())
    assert "error" not in resp.json()["text"]

    params = {"text": "analyze timeline"}
    resp = requests.post(BASE_URL + "/feed", data=params)
    assert resp.status_code == 200
    print(resp.json())

    params = {"text": "d 1"}
    resp = requests.post(BASE_URL + "/feed", data=params)
    assert resp.status_code == 200
    print(resp.json())
    assert "error" not in resp.json()["text"]

def test_start_end_feed():
    params = {"text": "s 12:30"}
    resp = requests.post(BASE_URL + "/feed", data=params)
    assert resp.status_code == 200
    print(resp.json())
    assert "error" not in resp.json()["text"]

    params = {"text": "e 12:35"}
    resp = requests.post(BASE_URL + "/feed", data=params)
    assert resp.status_code == 200
    print(resp.json())
    assert "error" not in resp.json()["text"]
    assert "00:05" in resp.json()["text"]


def test_create_list_delete_analyze_sleep_record():
    params = {"text": "12:30 12:35"}
    resp = requests.post(BASE_URL + "/sleep", data=params)
    assert resp.status_code == 200
    print(resp.json())
    assert "error" not in resp.json()["text"]

    params = {"text": "list"}
    resp = requests.post(BASE_URL + "/sleep", data=params)
    assert resp.status_code == 200
    print(resp.json())
    assert "error" not in resp.json()["text"]
    assert "12:30" in resp.json()["text"]
    assert "00:05" in resp.json()["text"]

    params = {"text": "analyze total"}
    resp = requests.post(BASE_URL + "/sleep", data=params)
    assert resp.status_code == 200
    print(resp.json())
    assert "error" not in resp.json()["text"]

    params = {"text": "analyze avg"}
    resp = requests.post(BASE_URL + "/sleep", data=params)
    assert resp.status_code == 200
    print(resp.json())
    assert "error" not in resp.json()["text"]

    params = {"text": "analyze timeline"}
    resp = requests.post(BASE_URL + "/sleep", data=params)
    assert resp.status_code == 200
    print(resp.json())

    params = {"text": "d 1"}
    resp = requests.post(BASE_URL + "/sleep", data=params)
    assert resp.status_code == 200
    print(resp.json())
    assert "error" not in resp.json()["text"]


def test_start_end_sleep():
    params = {"text": "s 12:30"}
    resp = requests.post(BASE_URL + "/sleep", data=params)
    assert resp.status_code == 200
    print(resp.json())
    assert "error" not in resp.json()["text"]

    params = {"text": "e 12:35"}
    resp = requests.post(BASE_URL + "/sleep", data=params)
    assert resp.status_code == 200
    print(resp.json())
    assert "error" not in resp.json()["text"]
    assert "00:05" in resp.json()["text"]


def test_create_list_delete_analyze_weight_record():
    params = {"text": "2021-05-18 3254"}
    resp = requests.post(BASE_URL + "/weight", data=params)
    assert resp.status_code == 200
    print(resp.json())
    assert "error" not in resp.json()["text"]

    params = {"text": "2021-05-22 3300"}
    resp = requests.post(BASE_URL + "/weight", data=params)
    assert resp.status_code == 200
    print(resp.json())
    assert "error" not in resp.json()["text"]

    params = {"text": "2021-05-25 3400"}
    resp = requests.post(BASE_URL + "/weight", data=params)
    assert resp.status_code == 200
    print(resp.json())
    assert "error" not in resp.json()["text"]

    params = {"text": "ls"}
    resp = requests.post(BASE_URL + "/weight", data=params)
    assert resp.status_code == 200
    print(resp.json())
    assert "error" not in resp.json()["text"]

    params = {"text": "analyze"}
    resp = requests.post(BASE_URL + "/weight", data=params)
    assert resp.status_code == 200
    print(resp.json())
    assert "error" not in resp.json()["text"]

    params = {"text": "d 1"}
    resp = requests.post(BASE_URL + "/weight", data=params)
    assert resp.status_code == 200
    print(resp.json())
    assert "error" not in resp.json()["text"]


def test_create_list_delete_analyze_poop_record():
    params = {"text": "2021-05-18"}
    resp = requests.post(BASE_URL + "/poop", data=params)
    assert resp.status_code == 200
    print(resp.json())
    assert "error" not in resp.json()["text"]

    params = {"text": "ls"}
    resp = requests.post(BASE_URL + "/poop", data=params)
    assert resp.status_code == 200
    print(resp.json())
    assert "error" not in resp.json()["text"]

    params = {"text": "d 1"}
    resp = requests.post(BASE_URL + "/poop", data=params)
    assert resp.status_code == 200
    print(resp.json())
    assert "error" not in resp.json()["text"]
