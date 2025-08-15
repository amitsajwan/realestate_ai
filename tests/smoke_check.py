import time, requests

BASE = 'http://127.0.0.1:8004'

def wait_ready(timeout=20):
    start = time.time()
    while time.time()-start < timeout:
        try:
            r = requests.get(BASE+'/', timeout=2)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(1)
    return False

assert wait_ready(), 'Server not ready'

# Login
r = requests.post(BASE+'/api/login', json={'email':'demo@mumbai.com','password':'demo123'}, timeout=5)
r.raise_for_status()
js = r.json()

# Leads
h = {'Authorization': f"Bearer {js['token']}", 'Content-Type':'application/json'}
rl = requests.get(BASE+'/api/leads', headers=h, timeout=5)
rl.raise_for_status()

# Properties
rp = requests.get(BASE+'/api/properties', headers=h, timeout=5)
rp.raise_for_status()

print('SMOKE: OK')
