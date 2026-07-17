var dagcomponentfuncs = window.dashAgGridComponentFunctions = window.dashAgGridComponentFunctions || {};

dagcomponentfuncs.feltkommentarIcon = function (props) {

    return React.createElement(
        "img",
        {
            src: "https://api.iconify.design/feather/message-square.svg",
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