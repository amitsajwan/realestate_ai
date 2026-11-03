"""Make the key pair for phone alerts (Web Push from Studio; app/modules/notifications/push.py). Run once, then put the two lines
in deploy/gcp/.env on the VM and restart the backend and the worker roles. Keep the private key secret. Changing the pair later
turns alerts off on every phone until Studio is opened there again.

    sudo docker compose exec -T -e PYTHONPATH=. backend python scripts/vapid_keys.py
"""
from app.modules.notifications.webpush import generate_keys

if __name__ == "__main__":
    public, private = generate_keys()
    print(f"VAPID_PUBLIC_KEY={public}")
    print(f"VAPID_PRIVATE_KEY={private}")
