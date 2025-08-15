import os
import time
import pytest
from playwright.sync_api import sync_playwright, expect

BASE_URL = os.getenv("BASE_URL", "http://localhost:8004")

@pytest.mark.order(1)
def test_login_and_nav():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # Login page
        page.goto(BASE_URL)
        page.fill("#email", "demo@mumbai.com")
        page.fill("#password", "demo123")
        page.click("button[type=submit]")

        # Wait for dashboard
        page.wait_for_url(f"{BASE_URL}/dashboard", timeout=10000)
        expect(page.locator("text=Real Estate CRM Dashboard")).to_be_visible()

        # Ensure sections toggle without console errors
        with page.expect_console_message() as _:
            page.click("text=Leads")
        expect(page.locator("#leadsSection")).to_be_visible()
        expect(page.locator("#dashboardSection")).not_to_be_visible()

        page.click("text=Properties")
        expect(page.locator("#propertiesSection")).to_be_visible()

        page.click("text=⚙️ Settings")
        expect(page.locator("#settingsSection")).to_be_visible()

        # Add lead modal opens/closes
        page.click("text=Leads")
        page.click("text=➕ Add New Lead")
        expect(page.locator("#addLeadModal")).to_be_visible()
        page.click("#addLeadModal .close")
        expect(page.locator("#addLeadModal")).not_to_be_visible()

        # Add property modal opens/closes
        page.click("text=Properties")
        page.click("text=🏠 Add New Property")
        expect(page.locator("#addPropertyModal")).to_be_visible()
        page.click("#addPropertyModal .close")
        expect(page.locator("#addPropertyModal")).not_to_be_visible()

        context.close()
        browser.close()
