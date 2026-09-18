from typing import Literal
from dash import html

class ModuleBase:
    _number: int = 0
    label: str
    module_name: str
    module_number: str
    module_id: str # module_name + module_number
    module_layout: html.Div

    def __init__(self, as_type: Literal["Tab", "Window"]) -> None:
        self.implemented_as = as_type
    
    def layout(self):
        ...
    
    

    