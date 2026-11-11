from playwright.sync_api import Page
from playwright.sync_api import expect

from e2e.harness import Ctx


def customize(page: Page, ctx: Ctx) -> None:
    macro_grid = page.locator('[id$="-macro-grid"] >> visible=true').first
    value_cell = macro_grid.locator(
        '.ag-center-cols-container [col-id="NyEngArbAreal"]'
    ).first
    expect(value_cell).to_be_visible()
    value_cell.click()

    observation_grid = page.locator('[id$="-observation-grid"] >> visible=true').first
    ident_cell = observation_grid.locator('[col-id="ident"].ag-cell').first
    expect(ident_cell).to_be_visible()
    ident = ident_cell.inner_text()
    ident_cell.click()

    page.get_by_role("button", name="Velg").locator("visible=true").first.click()
    page.get_by_role("button", name="Vis variabler").click()
    expect(page.locator("#var-ident")).to_have_value(ident)
    page.keyboard.press("Escape")
