from dash import Input
from dash import Output
from dash import State
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import computed_field


class EditableField(BaseModel):
    """Model specifying interactive configurations for individual microlayout input controls.

    Attributes:
        variable: The questionnaire form variable field name path.
        variabel_trigger: The Dash callback trigger property name. Defaults to "n_blur".
        id: Unique identifier for the element.
        type: The specific input type name (e.g. "input", "dropdown").
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)
    variable: str
    variabel_trigger: str = Field(default="n_blur")
    id: str
    type: str


class FieldCallbackContainer(BaseModel):
    """Metadata wrapper used by the MicroLayout AIO engine to auto-wire callbacks.

    Attributes:
        settings: The field configurations.
        parent_id: The ID of the parent element.
    """
    settings: EditableField
    parent_id: str

    def get_state(self, aio_id: str):
        """Generates the State dependency object for Dash callbacks.

        Args:
            aio_id: The isolated All-in-One container ID.

        Returns:
            A Dash State dependency.
        """
        return State({"comp_id": self._id, "aio": aio_id}, "value")

    def get_input(
        self,
        aio_id: str,
    ):
        """Generates the Input dependency object for Dash callbacks.

        Args:
            aio_id: The isolated All-in-One container ID.

        Returns:
            A Dash Input dependency.
        """
        return Input(
            {"comp_id": self._id, "aio": aio_id}, self.settings.variabel_trigger, allow_optional=True
        )

    def get_output(
        self,
        aio_id: str,
    ):
        """Generates the Output dependency object for Dash callbacks.

        Args:
            aio_id: The isolated All-in-One container ID.

        Returns:
            A Dash Output dependency.
        """
        return Output({"comp_id": self._id, "aio": aio_id}, "value")

    @computed_field
    @property
    def _id(self) -> str:
        return self.parent_id
