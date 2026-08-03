import requests


def send_discord_alert(webhook_url: str, title: str, message: str, color: int = 0xE01E5A) -> bool:
    """
    Sends a formatted alert to a Discord Webhook.
    Returns True on success (HTTP 2xx), False otherwise.
    """
    payload = {
        "embeds": [
            {
                "title": title,
                "description": message,
                "color": color,
                "footer": {"text": "Cloud Cost Alert Bot"},
            }
        ]
    }
    try:
        resp = requests.post(webhook_url, json=payload, timeout=10)
        return 200 <= resp.status_code < 300
    except requests.RequestException:
        return False
