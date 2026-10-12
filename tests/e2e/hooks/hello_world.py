from playwright.sync_api import Page
from playwright.sync_api import expect

from e2e.harness import Ctx


def customize(page: Page, ctx: Ctx) -> None:
    page.get_by_role("button", name="Vis variabler").click()
    page.locator("#var-Refnr").fill("1")
    page.keyboard.press("Escape")
    expect(page.locator(".offcanvas.show")).to_have_count(0)

    page.get_by_role("button", name="Get currently stored message").click()
    expect(page.locator('[id$="-message-holder"]')).to_have_value("Hello world!")
