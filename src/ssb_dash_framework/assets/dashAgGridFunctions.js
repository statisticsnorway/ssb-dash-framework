window.dashAgGridFunctions = window.dashAgGridFunctions || {};

// MacroModule
window.dashAgGridFunctions.MacroModule = {

    // === Function formatHeatmapValue (Format values based on row type) ===
    formatHeatmapValue(params, isPercentage) {
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
        if (isPercentage) {
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

        // Special handling for count row
        if (props.data && props.data.id === 'count_row') {
            return {
                color: 'black',
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

        // Special handling for count row
        if (props.data && props.data.id === 'count_row') {
            return {
                color: 'black',
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

    // === Function displayDiffColumnHighlight (Mark tilgang & avgang on the diff-column) ===
    displayDiffColumnHighlight(props) {
        if (!props.data) return {};

        const value = props.value;
        const field = props.colDef.field;

        // Only _diff columns should ever call this,
        // but this guard keeps it safe
        if (!field.endsWith("_diff")) return {};

        // tilgang / avgang still applies — but scoped to this column
        if (props.data.is_tilgang) {
            return {
                backgroundColor: "#c7f5c7",
                color: "black",
            };
        }

        if (props.data.is_avgang) {
            return {
                backgroundColor: "#ffc7c7",
                color: "black",
            };
        }

        return {};
    }

};
