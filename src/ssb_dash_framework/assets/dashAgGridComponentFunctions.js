const dagcomponentfuncs = window.dashAgGridComponentFunctions = window.dashAgGridComponentFunctions || {};

dagcomponentfuncs.feltkommentarIcon = function (props) {
    const isDarkMode = document.body.classList.contains("dark-mode");

    return React.createElement(
        "img",
        {
            src: `https://api.iconify.design/feather/message-square.svg?color=${isDarkMode ? "%23ffffff" : "%23274347"}`,
            className: "feltkommentar-ikon",
            width: 16,
            height: 16,
            style: {
                verticalAlign: "right",
                marginLeft: "6px",
                opacity: props.value ? 1 : 0.25
            }
        }
    );
};