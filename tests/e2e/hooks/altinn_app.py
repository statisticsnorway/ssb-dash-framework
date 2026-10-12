from playwright.sync_api import Page
from playwright.sync_api import expect

from e2e.harness import Ctx


def customize(page: Page, ctx: Ctx) -> None:
    page.get_by_role("button", name="Vis variabler").click()
    expect(page.locator("#var-periode")).to_have_value("2026")
    expect(page.locator("#var-ident")).to_have_value("ATF2134661")
    expect(page.locator("#var-altinnskjema")).to_have_value("RA-0745")
    page.keyboard.press("Escape")
    expect(page.locator(".offcanvas.show")).to_have_count(0)

    expect(
        page.get_by_role("gridcell", name="Bredspreder for bløtgjødsel med tankvogn")
    ).to_be_visible()
