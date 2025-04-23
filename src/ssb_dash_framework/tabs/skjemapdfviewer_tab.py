import logging

from dash import html

from ..modules.skjemapdfviewer import SkjemapdfViewer

logger = logging.getLogger(__name__)

class SkjemapdfViewerTab(SkjemapdfViewer):
    def __init__(self):
        super().__init__()

    def layout(self):
        layout = self.module_layout
        logger.debug("Generated layout")
        return layout