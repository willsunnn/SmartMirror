from collections import OrderedDict
import tkinter
import pathlib
from BaseWidget import BaseWidget
from Dimensions import Size, Conversion, Constraint


class LayoutManager:
    def __init__(self, size: {str: tuple}, widgets):
        self.widgets: {str: BaseWidget} = widgets
        self.conversion: Conversion = None
        self.set_conversion(size)
        self.window = tkinter.Tk()
        self.configure_window()
        self.constraints: [Constraint] = []

    def set_conversion(self, size):
        self.pixel_size = Size.size_from_str(size["pixel_size"][0]), Size.size_from_str(size["pixel_size"][1])
        self.physical_size = Size.size_from_str(size["physical_size"][0]), Size.size_from_str(size["physical_size"][1])
        conversions = self.pixel_size[0]/self.physical_size[0], self.pixel_size[1]/self.physical_size[1]
        assert conversions[0] == conversions[1], f"Ratio of pixel size to physical size is inconsistent along width and height\n\t{conversions[0]} and {conversions[1]} are not equal"
        self.conversion: Conversion = conversions[0]

    def configure_window(self):
        self.window.title = "MirrorGUI"
        self.window.config(background="#000000")
        self.window.geometry(f"{self.conversion.to_px(self.pixel_size[0])}x{self.conversion.to_px(self.pixel_size[1])}")
        self.window.resizable(0, 0)

    def get_widget(self, widget_id):
        return self.widgets[widget_id]

    def to_px(self, size: Size):
        return self.conversion.to_px(size)

    def get_unused_id(self, widget):
        class_name = type(widget).__name__
        i = 1
        while True:
            if f"{class_name}_[{i}]" not in self.widgets.keys():
                return f"{class_name}_[{i}]"
            else:
                i += 1

    def add_constraints(self, new_constraints):
        self.constraints += map(lambda const: Constraint.construct_constraint(self, const), new_constraints)

    def evaluate_constaints(self):
        for constraint in self.constraints:
            obj, prop, value = constraint.evaluate()
            obj.__setattr__(prop, value)

    def place_all(self):
        for widget_id, widget in self.widgets.items():
            (x, y), (width, height) = widget.get_rect()
            widget.place(x=x, y=y, width=width, height=height)

    def __str__(self):
        return f"LayoutManager Object:\n\tConversion = {self.conversion}\n\tPixel Size = {tuple(map(str, self.pixel_size))}\n\tPhysical Size = {tuple(map(str, self.physical_size))}"


class UpdateManager:
    def __init__(self, widgets):
        self.widgets = widgets

    def update_widgets(self):
        for widget_id, widget in self.widgets.items():
            widget.update_values()


class SmartMirror:
    # Manages the widget placement and updates implicitly through the LayoutManager and the UpdateManager
    @staticmethod
    def parse_json(file_name: pathlib.Path):
        import json
        return json.loads(" ".join(open(file_name)))

    def __init__(self, json_path):
        config = SmartMirror.parse_json(json_path)
        self.widgets: {str: BaseWidget} = OrderedDict()
        self.layout_manager: LayoutManager = LayoutManager(config["window_config"], self.widgets)
        self.update_manager: UpdateManager = UpdateManager(self.widgets)
        self.add_widgets(config["widgets"])

    def add_widgets(self, widgets_config):
        for widget in map(self.construct_widget, widgets_config):
            widget_id = widget.get_id()
            assert widget_id not in self.widgets.keys(), f"Error, ID already added\nAddedID = {widget_id}\n" + "Preexisting IDs:\n\t" + "\n\t".join([f"widgets[{widget_id}] = {widget}" for widget_id, widget in self.widgets.items()])
            self.widgets[widget_id] = widget
            self.layout_manager.add_constraints(widget.get_constraints())
        self.layout_manager.evaluate_constaints()
        self.layout_manager.place_all()

    def construct_widget(self, widget_config):
        if "subwidgets" not in widget_config:
            widget_config["subwidgets"] = None
        return BaseWidget(self, subwidgets=widget_config["subwidgets"], props=widget_config["props"], constraints=widget_config["constraints"])

    def __str__(self):
        return "Layout Manager = \n\t" + "\n\t".join(str(self.layout_manager).split("\n")) + "\nWidgets = \n\t" + str(self.widgets.items())

    def mainloop(self):
        self.add_update_checkers([self.layout_manager.evaluate_constaints, self.layout_manager.place_all], [1000, 1000])
        self.layout_manager.window.mainloop()

    def add_update_checkers(self, functions, update_times):
        class LoopMethod:
            def __init__(self, func, smart_mirror, update_milliseconds: int):
                self.sm = smart_mirror
                self.time = update_milliseconds
                self.func = func

            def __call__(self, *args, **kwargs):
                self.func(*args, **kwargs)
                self.sm.layout_manager.window.after(100, lambda: self.__call__(*args, **kwargs))

        for func, time in zip(functions, update_times):
            func = LoopMethod(func, self, time)
            func()


if __name__ == "__main__":
    sm = SmartMirror("config.json")
    print(sm)
    sm.mainloop()
