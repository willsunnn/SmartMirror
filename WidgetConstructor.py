from pathlib import Path
widgets_path = "./AddonWidgets"


def get_widget_folders(path: Path = widgets_path):
    return list(filter(lambda x: x.is_dir(), (Path(path) if isinstance(path, str) else path).iterdir()))


def get_import(directory: Path):
    return (lambda path, name: f"from {'.'.join(path.parts).rstrip('.py')} import {name}")(Path(widgets_path)/directory.stem, directory.stem)


def get_import_statements(files: [Path]=get_widget_folders(widgets_path)):
    return "\n".join(map(get_import, files))


from BaseWidget import BaseWidget
exec(get_import_statements())


def get_widget_dict(files: [Path] = get_widget_folders()):
    exec(get_import_statements(files))
    wd = {}
    for file in files:
        wd[file.stem] = eval(f"{file.stem}.{file.stem}")
    return wd


widgets = {"BaseWidget": BaseWidget}
widgets.update(get_widget_dict())


def construct_widget(parent, widget_config):
    widget_type = widgets[widget_config["name"]]
    return construct_widget_helper(widget_type, parent, widget_config)


def construct_widget_helper(widget_type, parent, widget_config):
    print(widget_type, parent, widget_config)
    return BaseWidget.construct_widget(parent, widget_config)
