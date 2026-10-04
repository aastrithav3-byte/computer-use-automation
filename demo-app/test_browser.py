from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)

    page = browser.new_page()

    page.goto("http://127.0.0.1:8000")

    print("Member Servicing System opened")

    page.get_by_label("Member ID").fill("12345")

    print("Member ID entered")

    page.get_by_role("button", name="Search Member").click()

    print("Search button clicked")

    input("Press Enter to close the browser...")

    browser.close()