from pathlib import Path
from Widgets.BaseWidget import BaseWidget
from Widgets.ClockWidget import ClockWidget
from Widgets.CalendarWidget import CalendarWidget
from Widgets.WeatherWidget import WeatherWidget


widgets_path = Path("Widgets/AddonWidgets")


widgets = {"BaseWidget": BaseWidget,
           "CalendarWidget": CalendarWidget,
           "ClockWidget": ClockWidget,
           "WeatherWidget": WeatherWidget}


def get_widget_folders(path: Path = widgets_path) -> [Path]:
    return list(filter(lambda x: x.is_dir(), (Path(path) if isinstance(path, str) else path).iterdir()))


def get_import_statements(files: [Path]):
    def get_import(directory: Path) -> str:
        return (lambda path, name: f"from {'.'.join(path.parts).rstrip('.py')} import {name}")(
            Path(widgets_path) / directory.stem, directory.stem)
    return "\n".join(map(get_import, files))


def get_widget_dict(files: [Path]):
    exec(get_import_statements(files))
    wd = {}
    for file in files:
        wd[file.stem] = eval(f"{file.stem}.{file.stem}")
    return wd


widgets.update(get_widget_dict(get_widget_folders()))


def construct_widget(parent, widget_config):
    widget_type = widgets[widget_config["name"]]
    try:
        assert widget_type.has_necessary_config()
    except AssertionError:
        print(f"Widget of type {widget_type} could not be constructed as it is missing some necesarry files.\n\t Widget will be constructed as a BaseWidget")
        widget_type = BaseWidget
    return widget_type(parent, widget_config.get("subwidgets", []), widget_config["constraints"], widget_config["props"])
