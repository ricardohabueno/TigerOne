from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://admin.avec.beauty/tarantino/admin")
    page.wait_for_timeout(3000) # wait 3s for JS to render
    html = page.content()
    with open("login.html", "w", encoding="utf-8") as f:
        f.write(html)
    browser.close()
