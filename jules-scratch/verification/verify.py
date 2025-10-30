from playwright.sync_api import sync_playwright

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    # Login
    page.goto("http://localhost:3000/login")
    page.get_by_placeholder("Enter your username").fill("testuser")
    page.get_by_role("button", name="Login").click()

    # Chat page
    page.wait_for_url("http://localhost:3000/")
    page.screenshot(path="jules-scratch/verification/verification.png")

    context.close()
    browser.close()

with sync_playwright() as playwright:
    run(playwright)
