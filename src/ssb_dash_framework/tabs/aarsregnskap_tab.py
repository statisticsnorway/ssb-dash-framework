import logging

from ..modules.aarsregnskap import Aarsregnskap

logger = logging.getLogger(__name__)


class AarsregnskapTab(Aarsregnskap):
    def __init__(self):
        super().__init__()

    def layout(self):
        layout = self.module_layout
        logger.debug("Generated layout")
        return layout
