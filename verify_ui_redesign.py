from playwright.sync_api import sync_playwright

def verify_ui_redesign():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1280, 'height': 800}) # Desktop view

        try:
            print("Navigating to app...")
            page.goto("http://localhost:5173")

            # Wait for key elements of the new design
            print("Waiting for new homepage elements...")
            # Check for the new hero title styling (using class, assuming CSS changes propagated)
            page.wait_for_selector(".hero-title", timeout=10000)

            # Check for "Parallels" text
            title = page.locator(".hero-title").inner_text()
            print(f"Found title: {title}")

            if "Parallels" in title:
                print("Verification Passed: Homepage loaded.")
            else:
                print("Verification Failed: Title mismatch.")

            # Take a screenshot of the Landing Page
            page.screenshot(path="verification_landing_redesign.png")
            print("Screenshot saved: verification_landing_redesign.png")

            # Now test the chat interface (click "Start Exploring")
            print("Clicking 'Start Exploring'...")
            page.click("text=Start Exploring")

            # Wait for Chat Interface to load (Sidebar should be visible)
            page.wait_for_selector(".sidebar", timeout=10000)

            # Check for the new "Parallels" empty state title
            page.wait_for_selector(".empty-title")
            empty_title = page.locator(".empty-title").inner_text()
            print(f"Found empty state title: {empty_title}")

            if "Parallels" in empty_title:
                 print("Verification Passed: Chat Interface loaded correctly.")

            # Take a screenshot of the Chat Interface
            page.screenshot(path="verification_chat_redesign.png")
            print("Screenshot saved: verification_chat_redesign.png")

        except Exception as e:
            print(f"Error during verification: {e}")
            page.screenshot(path="verification_error_redesign.png")
        finally:
            browser.close()

if __name__ == "__main__":
    verify_ui_redesign()
