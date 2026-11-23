import json

from playwright.sync_api import Page
from playwright.sync_api import Response
from playwright.sync_api import expect

from e2e.harness import Ctx


def _is_hb_run_response(response: Response) -> bool:
    return (
        response.url.endswith("/_dash-update-component")
        and "hb_run_button" in (response.request.post_data or "")
    )


def _is_hb_display_response(response: Response) -> bool:
    return (
        response.url.endswith("/_dash-update-component")
        and "hb_result_store" in (response.request.post_data or "")
        and "hb_run_button" not in (response.request.post_data or "")
    )


def _select_demo_unit(page: Page, unit_id: str, period: str = "2025") -> None:
    page.get_by_role("button", name="Vis variabler").click()
    page.locator("#var-ident").fill(unit_id)
    page.locator("#var-ident").press("Tab")
    expect(page.locator("#var-refnr")).to_have_value(
        f"hb-demo-{unit_id}-{period}"
    )
    page.keyboard.press("Escape")
    expect(page.locator(".offcanvas.show")).to_have_count(0)


def customize(page: Page, ctx: Ctx) -> None:
    page.get_by_role("button", name="Kjør HB-metoden").click()

    hb_result_graph = page.locator('[id$="-hb_result_graph"]')
    expect(hb_result_graph).to_be_visible()
    expect(
        page.locator('[id$="-hb_candidate_state_summary"]')
    ).to_have_text(    "Flagget: 1 · Ikke flagget: 9 · Ikke sammenlignbar: 0")

    flagged_trace_index = hb_result_graph.evaluate(
        """graph => {
            const plot = graph.querySelector(".js-plotly-plot");
            if (!plot || !Array.isArray(plot.data)) {
                throw new Error("HB result graph has no Plotly data.");
            }
            const traceIndex = plot.data.findIndex(trace => trace.name === "Flagget");
            if (traceIndex < 0) {
                throw new Error("HB result graph has no flagged-candidate trace.");
            }
            const candidateId = plot.data[traceIndex].customdata?.[0]?.[0];
            if (candidateId !== "900000007") {
                throw new Error(
                    `Expected 900000007 as the first flagged candidate, got ${candidateId}.`
                );
            }
            return traceIndex;
        }"""
    )
    flagged_candidate = hb_result_graph.locator(
        ".scatterlayer g.trace"
    ).nth(flagged_trace_index).locator(".points path.point").first
    expect(flagged_candidate).to_be_visible()
    point_bounds = flagged_candidate.bounding_box()
    assert point_bounds is not None
    page.mouse.click(
        x=point_bounds["x"] + point_bounds["width"] / 2,
        y=point_bounds["y"] + point_bounds["height"] / 2,
    )

    page.get_by_role("button", name="Vis variabler").click()
    expect(page.locator("#var-ident")).to_have_value("900000007")
    page.keyboard.press("Escape")
    expect(page.locator(".offcanvas.show")).to_have_count(0)

    page.locator("#main-layout-tab-list").get_by_text("Data editor").click()
    page.wait_for_load_state("networkidle")
    editor_value = page.locator('[id*="hb_demo_value"]')
    expect(editor_value).to_be_visible()
    expect(editor_value).to_have_value("200")
    expect(page.get_by_text("Tabellvelger")).to_have_count(0)
    expect(page.get_by_text("Get field for inforow failed")).to_have_count(0)

    with page.expect_response(
        lambda response: response.url.endswith("/_dash-update-component")
        and "hb_demo_value" in (response.request.post_data or "")
    ) as editor_update_response:
        editor_value.fill("40")
        editor_value.press("Tab")
    assert editor_update_response.value.ok, editor_update_response.value.text()
    save_button = page.get_by_role("button", name="Lagre redigering")
    expect(save_button).to_be_enabled()

    page.locator("#main-layout-tab-list").get_by_text("HB metoden").click()
    page.get_by_role("button", name="Kjør HB-metoden").click()
    expect(
        page.locator('[id$="-hb_candidate_state_summary"]')
    ).to_have_text("Flagget: 1 · Ikke flagget: 9 · Ikke sammenlignbar: 0")

    page.locator("#main-layout-tab-list").get_by_text("Data editor").click()
    save_button.click()
    edit_dialog = page.get_by_role("dialog")
    expect(edit_dialog).to_be_visible()
    page.get_by_role("button", name="Bekreft lagring").click()
    expect(page.get_by_text("Velg en årsak.")).to_be_visible()
    page.get_by_role("radio", name="Statistisk gjennomgang").check()
    page.get_by_role("button", name="Bekreft lagring").click()
    expect(page.get_by_text("Skriv en begrunnelse.")).to_be_visible()
    page.get_by_placeholder("Skriv begrunnelse for endringen").fill(
        "Kontrollert mot demonstrasjonsdata."
    )
    page.get_by_role("button", name="Bekreft lagring").click()
    expect(edit_dialog).to_be_hidden()

    with (
        page.expect_response(_is_hb_run_response) as hb_run_response,
        page.expect_response(_is_hb_display_response) as hb_display_response,
    ):
        page.locator("#main-layout-tab-list").get_by_text("HB metoden").click()
        page.get_by_role("button", name="Kjør HB-metoden").click()
    assert hb_run_response.value.ok
    hb_run_payload = hb_run_response.value.json()
    stored_hb_result = next(
        (
            component["data"]
            for component in hb_run_payload.get("response", {}).values()
            if isinstance(component, dict)
            and isinstance(component.get("data"), dict)
            and "hb_result_dataframe_json" in component["data"]
        ),
        None,
    )
    assert stored_hb_result is not None, (
        f"HB run response did not contain result data: {hb_run_payload!r}"
    )
    result_dataframe = json.loads(stored_hb_result["hb_result_dataframe_json"])
    unit_id_column_index = result_dataframe["columns"].index("unit_id")
    current_period_value_column_index = result_dataframe["columns"].index("value_2025")
    unit_007_row = next(
        row
        for row in result_dataframe["data"]
        if row[unit_id_column_index] == "900000007"
    )
    assert unit_007_row[current_period_value_column_index] == 40
    assert hb_display_response.value.ok
    page.wait_for_load_state("networkidle")
    candidate_traces = hb_result_graph.evaluate(
        """graph => {
            const plot = graph.querySelector(".js-plotly-plot");
            if (!plot || !Array.isArray(plot.data)) {
                throw new Error("HB result graph has no Plotly data.");
            }
            const traces = Array.isArray(plot._fullData) ? plot._fullData : plot.data;
            return traces
                .filter(trace => ["Flagget", "Ikke flagget"].includes(trace.name))
                .map(trace => ({
                    name: trace.name,
                    x: Array.from(trace.x || []),
                    customdata: Array.from(trace.customdata || [])
                }));
        }"""
    )
    plotted_values = [
        trace["x"][index]
        for trace in candidate_traces
        for index, point in enumerate(trace["customdata"])
        if point and point[0] == "900000007" and index < len(trace["x"])
    ]
    assert plotted_values == [40], (
        f"Expected HB graph value 40 for unit 900000007, "
        f"got {plotted_values!r} in {candidate_traces!r}."
    )

    _select_demo_unit(page, "900000003")
    page.locator("#main-layout-tab-list").get_by_text("Data editor").click()
    expect(editor_value).to_have_value("33")

    with page.expect_response(
        lambda response: response.url.endswith("/_dash-update-component")
        and "hb_demo_value" in (response.request.post_data or "")
    ) as switched_editor_update_response:
        editor_value.fill("20077")
        editor_value.press("Tab")
    assert switched_editor_update_response.value.ok
    expect(save_button).to_be_enabled()

    _select_demo_unit(page, "900000004")
    expect(editor_value).to_have_value("44")
    expect(save_button).to_be_disabled()

    page.locator("#main-layout-tab-list").get_by_text("HB metoden").click()
    graph_dimensions = hb_result_graph.evaluate(
        """graph => {
            const module = graph.closest(".tab-implementation");
            if (!module) {
                throw new Error("HB result graph is outside its module tab.");
            }
            return {
                graphWidth: graph.getBoundingClientRect().width,
                moduleWidth: module.getBoundingClientRect().width
            };
        }"""
    )
    assert graph_dimensions["graphWidth"] >= graph_dimensions["moduleWidth"] * 0.8
