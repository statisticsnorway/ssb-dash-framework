document.addEventListener("click", function (event) {
    const glossaryButton = event.target.closest(".glossary-button");
    const glossaryClose = event.target.closest(".glossary-closing");
    const glossary = event.target.closest(".ssb-glossary");

    // Klikk på Lukk
    if (glossaryClose) {
        const popup = glossaryClose.closest(".glossary-popup");

        if (popup) {
            popup.classList.remove("open");
        }

        return;
    }

    // Klikk på glossary-knappen
    if (glossaryButton) {
        const glossaryContainer = glossaryButton.closest(".ssb-glossary");
        const popup = glossaryContainer.querySelector(".glossary-popup");

        // Lukk eventuelle andre åpne glossary-popups
        document
            .querySelectorAll(".ssb-glossary .glossary-popup.open")
            .forEach(function (openPopup) {
                if (openPopup !== popup) {
                    openPopup.classList.remove("open");
                }
            });

        // Toggle denne
        popup.classList.toggle("open");

        return;
    }

    // Klikk utenfor glossary
    if (!glossary) {
        document
            .querySelectorAll(".ssb-glossary .glossary-popup.open")
            .forEach(function (popup) {
                popup.classList.remove("open");
            });
    }
});


document.addEventListener("focusin", function (event) {
    const glossary = event.target.closest(".ssb-glossary");

    if (glossary) {
        return;
    }

    document
        .querySelectorAll(".ssb-glossary .glossary-popup.open")
        .forEach(function (popup) {
            popup.classList.remove("open");
        });
});