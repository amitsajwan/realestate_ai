import os
import time
from playwright.sync_api import sync_playwright

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8003")

def test_onboarding_smoke():
	with sync_playwright() as p:
		browser = p.chromium.launch()
		page = browser.new_page()
		page.goto(f"{BASE_URL}/")
		page.click('text=onboarding', timeout=10000)
		assert page.is_visible('text=Agent Onboarding')
		page.fill('input[name="name"]', 'Smoke Agent')
		page.fill('input[name="email"]', f'smoke.{int(time.time())}@example.com')
		page.fill('input[name="whatsapp"]', '+911234567890')
		page.click('button[type="submit"]')
		browser.close()

