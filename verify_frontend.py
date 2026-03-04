from playwright.sync_api import sync_playwright

def verify_app():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            print("Navigating to app...")
            page.goto("http://localhost:5173")

            # Wait for the app to load (basic sanity check)
            # The landing page has "Parallels" text or similar.
            # HomePage.jsx has <h1 className="hero-title">Parallels</h1>

            print("Waiting for hero title...")
            page.wait_for_selector(".hero-title", timeout=10000)

            title = page.locator(".hero-title").inner_text()
            print(f"Found title: {title}")

            if "Parallels" in title:
                print("Verification Passed: Landing page loaded.")
            else:
                print("Verification Failed: Title mismatch.")

            # Take screenshot
            page.screenshot(path="verification_screenshot.png")
            print("Screenshot saved to verification_screenshot.png")

        except Exception as e:
            print(f"Error during verification: {e}")
            page.screenshot(path="verification_error.png")
        finally:
            browser.close()

if __name__ == "__main__":
    verify_app()
