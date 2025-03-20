from textual.screen import Screen
from textual.app import ComposeResult
from textual.containers import ScrollableContainer, Center
from textual.widgets import Static, Footer, Button, Input
from textual.binding import Binding
from pydantic import BaseModel

from settings import settings

class SettingsScreen(Screen):

    BINDINGS = [Binding("escape", "quit", "Back to main menu")]

    def compose(self) -> ComposeResult:
        yield Center(Static("[bold]Settings[/bold]\n", markup=True))
        self.container = ScrollableContainer()
        yield self.container
        yield Center(Button("Save Settings", id='save_button'))
        yield Footer()

    async def on_mount(self) -> None:
        self.build_settings_ui(settings)

    def build_settings_ui(self, obj: BaseModel, prefix="") -> None:
        for key, value in obj.model_dump().items():
            full_key = f"{prefix}{key}"
            
            if isinstance(value, dict):  
                self.container.mount(Static(f"[bold]{full_key}[/bold]:", classes="category"))
                self.build_settings_ui(getattr(obj, key), prefix=f"{full_key}-")
            else:
                input_widget = Input(value=str(value), id=f"input_{full_key}")
                self.container.mount(Static(f"{full_key}:"), input_widget)

    def action_quit(self) -> None:
        self.app.switch_mode("menu")
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save_button":
            self.save_settings()

    # TODO: More correctly, this should all be done in settings.py

    def save_settings(self) -> None:
        """Saves the updated settings values from inputs."""
        updated_values = {}

        for widget in self.container.query(Input):
            key = widget.id.replace("input_", "").replace('-', '.')
            raw_value = widget.value

            try:
                old_value = self.get_nested_value(settings, key)
                new_value = self.cast_value(raw_value, type(old_value))
                self.set_nested_value(settings, key, new_value)
                updated_values[key] = new_value
            except ValueError:
                self.app.notify(f"Invalid value for {key}: {raw_value}", severity="error")
                return

        # TODO: Actually update settings (see https://docs.pydantic.dev/latest/concepts/pydantic_settings/#in-place-reloading)
        self.app.notify("Settings saved successfully!", severity="info")

    def get_nested_value(self, obj: BaseModel, key: str):
        keys = key.split(".")
        for k in keys:
            obj = getattr(obj, k)
        return obj

    def set_nested_value(self, obj: BaseModel, key: str, value):
        keys = key.split(".")
        for k in keys[:-1]:
            obj = getattr(obj, k)
        setattr(obj, keys[-1], value)

    def cast_value(self, raw_value: str, expected_type):
        if expected_type == int:
            return int(raw_value)
        elif expected_type == float:
            return float(raw_value)
        elif expected_type == bool:
            return raw_value.lower() == 'true'
        return str(raw_value)