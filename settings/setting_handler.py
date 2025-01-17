from typing import Callable, Any, Dict, List

class SettingHandler:
    def __init__(self, key: str, label: str, default_value: Any, type: str, handler: Callable, options: List[Dict] = None):
        self.key = key
        self.label = label
        self.default_value = default_value
        self.type = type
        self.handler = handler
        self.options = options

    def get_value(self, settings_dict: Dict) -> Any:
        return settings_dict.get(self.key, self.default_value)

    def set_value(self, settings_dict: Dict, value: Any):
        settings_dict[self.key] = value

    def render_html(self) -> str:
        if self.type == 'checkbox':
            checked = 'checked' if self.default_value else ''
            return f'<label for="{self.key}">{self.label}:</label><input type="checkbox" id="{self.key}" {checked}><br>'
        elif self.type == 'text':
            return f'<label for="{self.key}">{self.label}:</label><input type="text" id="{self.key}" value="{self.default_value}"><br>'
        elif self.type == 'select':
            options_html = ''.join([f'<option value="{option["value"]}" {"selected" if option["value"] == self.default_value else ""}>{option["label"]}</option>' for option in self.options])
            return f'<label for="{self.key}">{self.label}:</label><select id="{self.key}">{options_html}</select><br>'
        else:
            return ''