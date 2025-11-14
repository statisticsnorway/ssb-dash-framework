window.dashAgGridFunctions = window.dashAgGridFunctions || {};

// MacroModule
window.dashAgGridFunctions.MacroModule = {

    // === Function displayDiffHeatMap (Heatmap colouring for a matrix-table with +/- 30% diff threshold) ===
    displayDiffHeatMap(props) {
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
        const field = props.colDef.field;
        const value = props.value;

        if (!props.data) return {};

        // convert to string for comparison
        const normalize = (v) => v !== null && v !== undefined ? String(v).trim() : "";

        if (field.endsWith('_x')) {
            // prev year
            const currentField = field.replace('_x', '');
            const currentValue = normalize(props.data[currentField]);
            const prevValue = normalize(value);

            return {
                backgroundColor: '#e8e9eb',
                color: 'black'
            };
        }

        // current year
        const prevField = field + '_x';
        const prevValue = normalize(props.data[prevField]);
        const currentValue = normalize(value);

        if (prevValue && currentValue && prevValue !== currentValue) {
            return {
                backgroundColor: '#fff8c7ff',
                color: 'black'
            };
        }

        return {};
    }

};