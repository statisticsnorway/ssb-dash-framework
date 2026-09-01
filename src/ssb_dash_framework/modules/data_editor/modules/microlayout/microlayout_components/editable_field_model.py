from dash import Input
from dash import Output
from dash import State
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import computed_field


class EditableField(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    variable: str
    variabel_trigger: str = Field(default="n_blur")
    id: str


class FieldCallbackContainer(BaseModel):
    settings: EditableField
    parent_id: str

    def get_state(self):
        return State(self._id, "value")

    def get_input(self):
        return Input(self._id, self.settings.variabel_trigger)

    def get_output(self):
        return Output(self._id, "value")

    @computed_field
    @property
    def _id(self) -> str:
        return self.parent_id
