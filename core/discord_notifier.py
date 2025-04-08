import requests

def send_discord_message(webhook_url, message):
    payload = {"content": message}
    requests.post(webhook_url, json=payload)

def send_discord_file(webhook_url, filepath, message=""):
    with open(filepath, 'rb') as f:
        files = {'file': f}
        payload = {"content": message}
        requests.post(webhook_url, data=payload, files=files)
