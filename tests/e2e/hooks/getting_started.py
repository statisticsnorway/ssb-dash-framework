from playwright.sync_api import Page
from playwright.sync_api import expect

from e2e.harness import Ctx


def customize(page: Page, ctx: Ctx) -> None:
    page.get_by_role("button", name="Vis variabler").click()
    expect(page.locator("#var-aar")).to_have_value("2025")
    expect(page.locator("#var-orgnr")).to_have_value("111111111")
    page.keyboard.press("Escape")
    expect(page.locator(".offcanvas.show")).to_have_count(0)

    expect(page.get_by_text("Turnover in 2025")).to_be_visible()

    page.get_by_role("button", name="Turnover over time").click()
    expect(page.get_by_text("Turnover for 111111111")).to_be_visible()
