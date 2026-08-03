import requests


def send_slack_alert(webhook_url: str, title: str, message: str, color: str = "#E01E5A") -> bool:
    """
    Sends a formatted alert to a Slack Incoming Webhook.
    Returns True on success (HTTP 200), False otherwise.
    """
    payload = {
        "attachments": [
            {
                "color": color,
                "title": title,
                "text": message,
                "footer": "Cloud Cost Alert Bot",
            }
        ]
    }
    try:
        resp = requests.post(webhook_url, json=payload, timeout=10)
        return resp.status_code == 200
    except requests.RequestException:
        return False
