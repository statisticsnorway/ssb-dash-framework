import logging

from ..modules.skjemapdfviewer import SkjemapdfViewer

logger = logging.getLogger(__name__)


class SkjemapdfViewerTab(SkjemapdfViewer):
    def __init__(self, pdf_folder_path, form_identifier="skjemaversjon"):
        super().__init__(form_identifier, pdf_folder_path)

    def layout(self):
        layout = self.module_layout
        logger.debug("Generated layout")
        return layout
