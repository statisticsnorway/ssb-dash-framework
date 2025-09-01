"""A set of modules creating an Altinn editor module with a lot of functionality.

It has a main view that acts as an organizer for several submodules with specific functionality. These can be modified, removed or replaced. It is also possible to add your own submodules to suit your needs.
"""

from .altinn_editor_main_view import AltinnSkjemadataEditor

__all__ = [
    "AltinnSkjemadataEditor",
]
