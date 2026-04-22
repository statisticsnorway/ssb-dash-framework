var dagcomponentfuncs = window.dashAgGridComponentFunctions = window.dashAgGridComponentFunctions || {};

dagcomponentfuncs.DropdownRenderer = function(props) {
    if (!props || !props.data || !props.colDef) {
    return React.createElement("span", {}, "");
    }

    const staticValues = props.colDef.cellRendererParams && props.colDef.cellRendererParams.values;
    const optionsField = props.colDef.cellRendererParams && props.colDef.cellRendererParams.optionsField;

    // If this row has per-row options, show dropdown
    let values = null;
    if (optionsField && props.data[optionsField]) {
        let rowOptions = props.data[optionsField];
        if (typeof rowOptions === "string") rowOptions = JSON.parse(rowOptions);
        const valueField = props.colDef.cellRendererParams.valueField || "code";
        const labelField = props.colDef.cellRendererParams.labelField || "name";
        values = rowOptions.map(o => ({ label: `${o[valueField]} ${o[labelField]}`, value: o[valueField] }));
    } else if (staticValues) {
        values = staticValues.map(v => ({ label: v, value: v }));
    }

    // If no options for this row, just render plain text
    if (!values || values.length === 0) {
        return React.createElement("span", {}, props.value || "");
    }

    function onChange(e) {
        const val = e.target.value === "" ? null : e.target.value;
        if (props.node && typeof props.node.setDataValue === "function") {
            props.node.setDataValue(props.colDef.field, val);
        }
    }

    return React.createElement(
        "select",
        {
            value: props.value || "",
            onChange: onChange,
            onClick: (e) => e.stopPropagation(),
            style: {
                width: "100%",
                height: "100%",
                borderRadius: "999px",
                padding: "2px 8px",
                border: "1px solid #dee2e6",
                backgroundColor: props.value ? "#e7f1ff" : "#f8f9fa",
                color: props.value ? "#000" : "#6c757d",
                fontWeight: "500",
                cursor: "pointer"
            }
        },
        [
            React.createElement("option", { value: "" }, "Velg..."),
            ...values.map(v =>
                React.createElement("option", { key: v.value, value: v.value }, v.label)
            )
        ]
    );
};

window.dashAgGridFunctions = window.dashAgGridFunctions || {};

/* -----------------------------------------------------------------------
 * Right-click → copy cell value for all AG Grid tables in the app.
 * Applies globally.
 * ----------------------------------------------------------------------- */
(function () {
    function showCopyNotification(value) {
        var container = document.getElementById('alert-container-bottom-left');
        if (!container) return;
        var now = new Date();
        var ts = now.getFullYear() + '-' +
            String(now.getMonth() + 1).padStart(2, '0') + '-' +
            String(now.getDate()).padStart(2, '0') + ' ' +
            String(now.getHours()).padStart(2, '0') + ':' +
            String(now.getMinutes()).padStart(2, '0') + ':' +
            String(now.getSeconds()).padStart(2, '0');
        var el = document.createElement('div');
        el.className = 'alert alert-info mb-2';
        el.setAttribute('role', 'alert');
        var small = document.createElement('small');
        small.className = 'text-muted';
        small.textContent = ts + ': ';
        el.appendChild(small);
        el.appendChild(document.createTextNode('Kopiert: ' + value));
        container.appendChild(el);
        setTimeout(function () { if (el.parentNode) el.parentNode.removeChild(el); }, 4000);
    }

    document.addEventListener('contextmenu', function (e) {
        if (typeof e.target.closest !== 'function') return;
        var cell = e.target.closest('.ag-cell') || e.target.closest('[col-id]');
        if (!cell) return;
        e.preventDefault();
        e.stopPropagation();
        var valueEl = cell.querySelector('.ag-cell-value') || cell;
        var value = (valueEl.textContent || '').trim();
        navigator.clipboard.writeText(value).catch(function () {
            var ta = document.createElement('textarea');
            ta.value = value;
            ta.style.cssText = 'position:fixed;opacity:0';
            document.body.appendChild(ta);
            ta.select();
            document.execCommand('copy');
            document.body.removeChild(ta);
        });
        showCopyNotification(value);
    }, true);

    console.log('[ag-grid copy] context menu listener registered');
}());

// MacroModule
window.dashAgGridFunctions.MacroModule = {

    // === Function formatHeatmapValue (Format values based on row type) ===
    formatHeatmapValue(params, tallvisning) {
        const value = params.value;

        if (value === null || value === undefined) {
            return '';
        }

        // Special handling for count row - just show number with thousand separator
        if (params.data && params.data.id === 'count_row') {
            return value.toLocaleString('nb-NO', {
                minimumFractionDigits: 0,
                maximumFractionDigits: 0
            });
        }

        // Regular cells - format as percentage or number
        if (tallvisning === 1) {
            return value.toLocaleString('nb-NO', {
                style: 'percent',
                minimumFractionDigits: 1,
                maximumFractionDigits: 1
            });
        } else {
            return value.toLocaleString('nb-NO', {
                minimumFractionDigits: 0,
                maximumFractionDigits: 0
            });
        }
    },

    // === Function formatDetailGridValue (Format numeric values in detail grid) ===
    formatDetailGridValue(params) {
        const value = params.value;

        if (value === null || value === undefined || value === '') {
            return '';
        }

        // Format as number with thousand separator
        return value.toLocaleString('nb-NO', {
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        });
    },

    // === Function displayDiffHeatMap (Heatmap colouring for a matrix-table with +/- 30% diff threshold) ===
    displayDiffHeatMap(props) {

        // Special handling for count row — inherit color so dark mode works
        if (props.data && props.data.id === 'count_row') {
            return {
                color: 'inherit',
            };
        }

        const val = props.value;

        if (val === null || val === undefined || isNaN(val)) {
            return {};
        }

        const threshold = 0.3;
        const normalized = val / threshold;

        // base colors
        const red = [252, 195, 174];     // normal red
        const blue = [180, 213, 250];    // normal blue
        const white = [255, 255, 255];   // white background

        // darker shades for beyond 30% threshold
        const darkRed = [252, 142, 104];
        const darkBlue = [126, 165, 252];

        let r, g, b;

        if (normalized >= 1) {
            // beyond positive threshold — dark blue
            r = darkBlue[0];
            g = darkBlue[1];
            b = darkBlue[2];
        } else if (normalized <= -1) {
            // below negative threshold — use dark red
            r = darkRed[0];
            g = darkRed[1];
            b = darkRed[2];
        } else if (normalized >= 0) {
            // normal range: interpolate white to blue
            let clamped = Math.min(normalized, 1);
            r = white[0] * (1 - clamped) + blue[0] * clamped;
            g = white[1] * (1 - clamped) + blue[1] * clamped;
            b = white[2] * (1 - clamped) + blue[2] * clamped;
        } else {
            // normal range: interpolate white to red
            let clamped = Math.max(normalized, -1);
            r = white[0] * (1 + clamped) + red[0] * -clamped;
            g = white[1] * (1 + clamped) + red[1] * -clamped;
            b = white[2] * (1 + clamped) + red[2] * -clamped;
        }

        return {
            backgroundColor: `rgb(${Math.round(r)}, ${Math.round(g)}, ${Math.round(b)})`,
            color: 'black',
        };
    },

    // === Function displaySimpleHeatMap (Simple 2-choice (cold/warm for neg/pos) heatmap) ===
    displaySimpleHeatMap(props) {

        // Special handling for count row — inherit color so dark mode works
        if (props.data && props.data.id === 'count_row') {
            return {
                color: 'inherit',
            };
        }

        const val = props.value;

        if (val === null || val === undefined || isNaN(val)) {
            return {};
        }

        // clamp value to [-1, 1] for interpolation
        const clamped = Math.max(-1, Math.min(1, val));

        // base colors
        const red = [252, 195, 174];
        const blue = [180, 213, 250];
        const white = [255, 255, 255];

        let r, g, b;

        if (clamped >= 0) {
            // interpolate from white to blue
            r = white[0] * (1 - clamped) + blue[0] * clamped;
            g = white[1] * (1 - clamped) + blue[1] * clamped;
            b = white[2] * (1 - clamped) + blue[2] * clamped;
        } else {
            // interpolate from white to red
            r = white[0] * (1 + clamped) + red[0] * -clamped;
            g = white[1] * (1 + clamped) + red[1] * -clamped;
            b = white[2] * (1 + clamped) + red[2] * -clamped;
        }

        return {
            backgroundColor: `rgb(${Math.round(r)}, ${Math.round(g)}, ${Math.round(b)})`,
            color: 'black',
        };
    },

    // === Function displayDiffHighlight (Compare current cell's value to previous year, highlight if different) ===
    displayDiffHighlight(props) {

    if (!props.data) return {};

    const field = props.colDef.field;
    const value = props.value;

    const normalize = (v) =>
        v !== null && v !== undefined ? String(v).trim() : "";

    // special handling for naring_b / naring_f
    if (field === "naring_b" || field === "naring_f") {
        const currentVal = normalize(value);
        const prevVal = normalize(props.data[field + "_x"]);

        const currentPrefix = currentVal.substring(0, 2); // first 2 digits
        const prevPrefix = prevVal.substring(0, 2);

        // CASE A: prefix changed → darker yellow
        if (currentPrefix && prevPrefix && currentPrefix !== prevPrefix) {
            return {
                backgroundColor: "#ffe491ff",
                color: "black",
            };
        }

        // CASE B: prefix same → normal diff behaviour
        if (prevVal && currentVal && prevVal !== currentVal) {
            return {
                backgroundColor: "#fff8c7ff", // light yellow
                color: "black"
            };
        }

        return {}; // no change
    }

    const prevField = field + "_x";
    const prevValue = normalize(props.data[prevField]);
    const currentValue = normalize(value);

    if (prevValue && currentValue && prevValue !== currentValue) {
        return {
            backgroundColor: "#fff8c7ff",
            color: "black"
        };
    }

    return {};

    },

     // === Function displayNaringRowMismatch (Grey out row if first 2 digits of naring_b and naring_f differ) ===
    displayNaringRowMismatch(props) {
        if (!props.data) return false;

        const naringB = props.data.naring_b;
        const naringF = props.data.naring_f;

        // if either value is missing, no styling
        if (!naringB || !naringF) return false;

        // compare first 2 digits
        const prefixB = String(naringB).substring(0, 2);
        const prefixF = String(naringF).substring(0, 2);

        return prefixB !== prefixF;
    },

    // === Function showClickPopup (Show confirmation popup when a name/orgnr cell is clicked in the detail grid) ===
    showClickPopup(cellClicked, rowData, orgnrFCol, orgnrBCol, namedCol) {
        var noShow = [null, '', {display: 'none'}];
        if (!cellClicked || !rowData) return noShow;

        var colId = cellClicked.colId;
        var rowId = cellClicked.rowId;
        if (rowId == null || [orgnrFCol, orgnrBCol, namedCol].indexOf(colId) === -1) {
            return noShow;
        }

        var rowIdx = parseInt(rowId);
        if (isNaN(rowIdx) || rowIdx >= rowData.length) return noShow;

        var row = rowData[rowIdx];
        var navn = row[namedCol] || '';
        var label;
        if (colId === orgnrBCol) {
            label = 'Bedrift: ' + navn + ' (' + (row[orgnrBCol] || '') + ')';
        } else {
            label = 'Foretak: ' + navn + ' (' + (row[orgnrFCol] || '') + ')';
        }

        var pendingData = {rowId: rowId, colId: colId, rowData: row};

        // Position relative to the detail grid container so the popup
        // scrolls with the page instead of floating over it.
        var containerEl = document.querySelector('.macromodule-detail-grid-container');
        var style;
        if (containerEl) {
            var rect = containerEl.getBoundingClientRect();
            var relX = (window._macroModuleLastClickX || 0) - rect.left;
            var relY = (window._macroModuleLastClickY || 0) - rect.top;
            style = {
                display: 'flex',
                position: 'absolute',
                top: (relY + 12) + 'px',
                left: relX + 'px',
                zIndex: '9999'
            };
        } else {
            style = {
                display: 'flex',
                position: 'fixed',
                top: ((window._macroModuleLastClickY || 0) + 12) + 'px',
                left: (window._macroModuleLastClickX || 0) + 'px',
                zIndex: '9999'
            };
        }
        return [pendingData, label, style];
    },

    // === Function hidePopupOnClear (Hide the confirmation popup when pending data is cleared) ===
    hidePopupOnClear(pendingData) {
        if (!pendingData) return {display: 'none'};
        return window.dash_clientside.no_update;
    },

    // === Function displayDiffColumnHighlight (Mark tilgang & avgang on the diff-column) ===
    displayDiffColumnHighlight(props) {
        if (!props.data) return {};

        const field = props.colDef.field;

        const isDiffColumn = field.endsWith("_diff");
        const isExitHighlightField =
            (field === "orgnr_b" || field === "navn") &&
            props.data.is_avgang &&
            props.data.is_exiter;

        // Guard: only apply to allowed columns
        if (!isDiffColumn && !isExitHighlightField) return {};

        // tilgang (still only for diff columns)
        if (isDiffColumn && props.data.is_tilgang) {
            return {
                backgroundColor: "#c7f5c7",
                color: "black",
            };
        }

        // avgang (diff columns OR exiter name/orgnr)
        if (props.data.is_avgang) {
            return {
                backgroundColor: "#ffc7c7",
                color: "black",
            };
        }

        return {};
    }
};

// Track last mouse click position so the popup can be anchored to the clicked cell
document.addEventListener('click', function(e) {
    window._macroModuleLastClickX = e.clientX;
    window._macroModuleLastClickY = e.clientY;
});
