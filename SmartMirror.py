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


class LoopMethod:
    def __init__(self, func, window, update_milliseconds: int):
        self.window = window
        self.time = update_milliseconds
        self.func = func

    def __call__(self, *args, **kwargs):
        self.func(*args, **kwargs)
        self.window.after(self.time, lambda: self.__call__(*args, **kwargs))


class UpdateManager:
    def __init__(self, smart_mirror):
        self.smart_mirror = smart_mirror

    def add_update_checkers(self, funcs, times, *args, **kargs):
        for func, time in zip(funcs, times):
            self.add_update_checker(func, time, *args, **kargs)

    def add_update_checker(self, func, time, *args, **kargs):
        func = LoopMethod(func, self.smart_mirror.get_window(), time)
        func(*args, **kargs)

    def add_widget_updater(self, widget, update_time, *args, **kargs):
        self.add_update_checker(widget.update_values, update_time, *args, **kargs)


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
        self.update_manager: UpdateManager = UpdateManager(self)
        self.add_widgets(map(lambda w: BaseWidget.construct_widget(self, w), config["widgets"]))

        self.layout_manager.evaluate_constaints()
        self.layout_manager.place_all()

    def get_window(self):
        return self.layout_manager.window

    def get_unused_id(self, w):
        return self.layout_manager.get_unused_id(w)

    def add_widgets(self, widgets):
        for widget in widgets:
            self.add_widget(widget)

    def add_widget(self, widget):
        widget_id = widget.get_id()
        assert widget_id not in self.widgets.keys(), f"Error, ID already added\nAddedID = {widget_id}\n" + "Preexisting IDs:\n\t" + "\n\t".join(
            [f"widgets[{widget_id}] = {widget}" for widget_id, widget in self.widgets.items()])
        self.widgets[widget_id] = widget
        self.add_constraints(widget.get_own_constraints())
        self.add_update_checker(widget)
        self.add_widgets(widget.subwidgets)

    def __str__(self):
        return "Layout Manager = \n\t" + "\n\t".join(str(self.layout_manager).split("\n")) + "\nWidgets = \n\t" + str(self.widgets.items())

    def mainloop(self):
        self.update_manager.add_update_checkers([self.layout_manager.evaluate_constaints, self.layout_manager.place_all], [1000, 1000])
        self.layout_manager.window.mainloop()

    def add_constraints(self, constraints):
        self.layout_manager.add_constraints(constraints)

    def add_update_checker(self, widget):
        if widget.get_update_time() is not None:
            self.update_manager.add_widget_updater(widget, widget.get_update_time())

if __name__ == "__main__":
    sm = SmartMirror("config.json")
    print(sm)
    sm.mainloop()
