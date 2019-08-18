from collections import OrderedDict, defaultdict
import tkinter
import pathlib
from Widgets.BaseWidget import BaseWidget
from Widgets import WidgetConstructor
from Widgets.Dimensions import Size, Conversion, Constraint


class LayoutManager:
    """
    Class to manage the layout of individual widgets
    Allows widgets to reference properties of other widgets to allow for dynamic sizing
    """

    #################
    # Setup Methods #
    #################

    def __init__(self, parent, size: {str: tuple}, colors: {str: str}):
        """
        Initializes a layout manager object that manages the widgets of parents.widgets

        :param parent: should be the SmartMirror object that has the property widgets
        :param size: see LayoutManager.set_conversion
        """
        self.widgets: {str: BaseWidget} = parent.widgets
        self.conversion: Conversion = None
        self.physical_size, self.pixel_size = None, None
        self.set_conversion(size)
        self.colors = colors
        self.window = tkinter.Tk()
        self.configure_window()
        self.constraints: OrderedDict = OrderedDict()

    def set_conversion(self, size: {str: [str, str]}) -> None:
        """
        takes the dictionary and constructs two tuples for the different size variables, as well as a conversion object
        for the layout manager to convert between different units of measurement

        :param size: should be in the format {"pixel_size": (a, b), "physical_size": (c, d)}
            where a, b, c, d are strings that can be converted into Size objects
        """
        self.pixel_size = Size.size_from_str(size["pixel_size"][0]), Size.size_from_str(size["pixel_size"][1])
        self.physical_size = Size.size_from_str(size["physical_size"][0]), Size.size_from_str(size["physical_size"][1])
        conversions = self.pixel_size[0]/self.physical_size[0], self.pixel_size[1]/self.physical_size[1]
        assert conversions[0] == conversions[1], f"Ratio of pixel size to physical size is inconsistent along width and height\n\t{conversions[0]} and {conversions[1]} are not equal"
        self.conversion: Conversion = conversions[0]

    def configure_window(self) -> None:
        """Sets the default settings for the tkinter window"""
        self.window.title = "MirrorGUI"
        self.window.config(background=self.colors["background_color"])
        self.window.geometry(f"{self.conversion.to_px(self.pixel_size[0])}x{self.conversion.to_px(self.pixel_size[1])}")
        self.window.resizable(0, 0)

    ##################
    # Layout Methods #
    ##################

    def add_constraints(self, new_constraints: [Constraint]) -> None:
        for constraint in new_constraints:
            assert constraint.get_identifier() not in self.constraints
            self.constraints[constraint.get_identifier()] = constraint

    def add_str_constraints(self, new_constraints: [str]) -> None:
        """
        Constructs and adds a constraint for each string description in new_constraints
        :param new_constraints: contains strings that follow the format necessary for Constraint.construct_constraint
        """
        self.add_constraints(map(lambda c: Constraint.construct_constraint(self, c), new_constraints))

    def evaluate_constraints(self) -> None:
        """
        evaluates each constraint's value and sets the corresponding object's property to that value
        constraints are evaluated in the order they are added, with a constraint's dependent constraints
        being evaluated before it
        """
        evaluated = defaultdict(lambda: False)
        for key in self.constraints:
           self.evaluate_constraint(key, evaluated)

    def evaluate_constraint(self, key: (str, str), evaluated):
        """evaluates an individual constraint and its dependent constraints
        helper method of LayoutManager.evaluate_constraints"""
        if not evaluated[key]:
            for dependent_key in self.constraints[key].get_dependents():
                if dependent_key in self.constraints: self.evaluate_constraint(dependent_key, evaluated)
            (obj, prop), value = self.constraints[key].evaluate()
            evaluated[key] = True
            obj.__setattr__(prop, value)

    def place_all(self) -> None:
        """positions all the widgets in the window based on their positions defined from the constraints"""
        for widget_id, widget in self.widgets.items():
            (x, y), (width, height) = widget.get_rect()
            widget.place(x=x, y=y, width=width, height=height)

    ##################
    # Helper Methods #
    ##################

    def get_window(self) -> tkinter.Tk:
        """Return the window that all the widgets are contained within"""
        return self.window

    def get_colors(self) -> {str: str}:
        """returns the dictionary of colors"""
        return self.colors

    def get_widget(self, widget_id: str) -> BaseWidget:
        """
        returns the widget associated with the widget_id so that its properties may be referenced

        :param widget_id: must be a key in SmartMirror's widgets OrderedDict
        :return: returns the widget associated with the widget id
        """
        return self.widgets[widget_id]

    def to_px(self, size: Size) -> int:
        """returns the int number of pixels the Size object represents in the given layout"""
        return self.conversion.to_px(size)

    def get_unused_id(self, widget) -> str:
        """
        generates an unused ID for a widget in the scenario an ID was not defined in the widget's props

        :param widget: widget is the widget the ID will be assigned to
        :return: returns an ID that should be unique to the widget
        """
        class_name = type(widget).__name__
        i = 1
        while True:
            if f"{class_name}_[{i}]" not in self.widgets.keys():
                return f"{class_name}_[{i}]"
            else:
                i += 1

    def __str__(self) -> str:
        """gives details about the LayoutManager's sizes, conversions and constraints"""
        return f"\nLayoutManager Object:\n\tConversion = {self.conversion}\n\tPixel Size = {tuple(map(str, self.pixel_size))}\n\tPhysical Size = {tuple(map(str, self.physical_size))}\n\tConstraints=[\n\t\t"+",\n\t\t".join(map(lambda c: str(c), self.constraints))+"]"


class LoopMethod:
    """decorator used by update manager to schedule repeated function calls in a tkinter window"""
    def __init__(self, func, window, update_milliseconds: int, *args, **kargs):
        self.window = window
        self.time = update_milliseconds
        self.func = func
        self.next_args = args
        self.next_kargs = kargs

    def __call__(self):
        """
        calls the function itself, and then schedules the same function call afterwards
        when the function is first called, it should return the args and kargs of the next method call
        """
        returned_value = self.func(*self.next_args, **self.next_kargs)
        if returned_value is not None:
            self.next_kargs, self.next_kargs = returned_value
        self.window.after(self.time, self.__call__)


class UpdateManager:
    """Class used to keep track of what widgets to update and when"""

    def __init__(self, smart_mirror):
        """
        Initializes an UpdateManager used to keep track of the widgets in smart_mirror.widgets

        :param smart_mirror: smart_mirror has a property widgets that has a method get_window that returns the root tk
        """
        self.smart_mirror = smart_mirror

    def add_update_checkers(self, funcs, times, *args, **kwargs) -> None:
        """
        Adds update checkers for each func and time (in ms)
        All methods would be called with the same args and kwargs if provided
        """
        for func, time in zip(funcs, times):
            self.add_update_checker(func, time, *args, **kwargs)

    def add_update_checker(self, func, time, *args, **kwargs) -> None:
        """
        Adds an update checker for the given func that executes every time (in ms)
        func would be called with the given args and kwargs
        """
        func(*args, **kwargs)
        LoopMethod(func, self.smart_mirror.get_window(), time)(*args, **kwargs)

    def add_widget_updater(self, widget, update_time=None) -> None:
        """Specific case of add_update_checker that registers the widget's update_values function"""
        if update_time is not None:
            self.add_update_checker(widget.update_values, update_time)


class SmartMirror:
    """
    Object that manages the entire GUI and Model of the widgets
    Manages the widget placement implicitly through the LayoutManager
    Manages the widget updates implicitly through the UpdateManager
    """

    # this value is in milliseconds; it determines how often constraints should be reevaluated
    WIDGET_LOCATION_REFRESH = 200

    #################
    # Setup Methods #
    #################

    def __init__(self, json_path: pathlib.Path):
        """
        Initializes the SmartMirror and all its sub-components based on the config in the json file at the given path

        :param json_path: points to a json that is formatted correctly
        """
        config = SmartMirror.parse_json(json_path)
        self.widgets: {str: BaseWidget} = OrderedDict()
        self.layout_manager: LayoutManager = LayoutManager(self, config["window_config"], config["colors"])
        self.update_manager: UpdateManager = UpdateManager(self)
        self.add_widgets(map(self.construct_widget, config["widgets"]))

        self.layout_manager.evaluate_constraints()
        self.layout_manager.place_all()

    def mainloop(self):
        """Adds all the method checkers and begins the tkinter window loop"""
        self.update_manager.add_update_checkers(
            [self.layout_manager.evaluate_constraints, self.layout_manager.place_all], [SmartMirror.WIDGET_LOCATION_REFRESH, SmartMirror.WIDGET_LOCATION_REFRESH])
        self.layout_manager.window.mainloop()

    #######################
    # Widget Construction #
    #######################

    def construct_widget(self, widget_config: []):
        """passes widget construction to the widget constructor"""
        return WidgetConstructor.construct_widget(self, widget_config)

    def add_widgets(self, widgets: [BaseWidget]) -> None:
        """Adds all the widgets and their corresponding subwidgets, constraints, and update checkers"""
        for widget in widgets:
            self.add_widget(widget)

    def add_widget(self, widget: BaseWidget) -> None:
        """Adds a widget and its corresponding subwidgets, constraints, and update checkers"""
        widget_id = widget.get_id()
        assert widget_id not in self.widgets.keys(), f"Error, ID already added\nAddedID = {widget_id}\n" + "Preexisting IDs:\n\t" + "\n\t".join(
            [f"widgets[{widget_id}] = {widget}" for widget_id, widget in self.widgets.items()])
        self.widgets[widget_id] = widget
        self.add_str_constraints(widget.get_own_constraints())
        self.add_update_checker(widget)
        self.add_widgets(widget.subwidgets)

    def add_constraints(self, constraints: [Constraint]) -> None:
        """Passes the given constraint descriptions to the LayoutManager to be constructed and handled"""
        self.layout_manager.add_constraints(constraints)

    def add_str_constraints(self, constraints: [str]) -> None:
        """Passes the given constraint descriptions to the LayoutManager to be constructed and handled"""
        self.layout_manager.add_str_constraints(constraints)

    def add_update_checker(self, widget: BaseWidget) -> None:
        """Registers the widget in the UpdateManager so that its value can be updated over time"""
        self.update_manager.add_widget_updater(widget, widget.update_time)

    ####################
    # Protocol Methods #
    ####################

    def get_window(self) -> tkinter.Tk:
        """
        returns the tkinter window that the GUI exists in

        method required by UpdateManager to schedule regular method calls
        method required by BaseWidget as the tkinter frame requires a parent to be constructed within
        """
        return self.layout_manager.get_window()

    def get_unused_id(self, w) -> str:
        """
        see LayoutManager.get_unused_id:
            generates an unused ID for a widget in the scenario an ID was not defined in the widget's props
        """
        return self.layout_manager.get_unused_id(w)

    def get_colors(self) -> {str: str}:
        """returns the dictionary of colors"""
        return self.layout_manager.get_colors()

    ##################
    # Helper Methods #
    ##################

    @staticmethod
    def parse_json(file_name: pathlib.Path or str):
        """returns the object constructed from the json file at the given path"""
        import json
        return json.loads(" ".join(open(file_name)))

    def __str__(self):
        """gives details about the SmartMirror's LayoutManager and Widgets"""
        return "\nLayout Manager = " + "\n\t".join(str(self.layout_manager).split("\n")) + "\nWidgets = \n\t" + "\n\t".join(map(lambda t: f"{t[0]}\t:\t{t[1]}", self.widgets.items())) +"\n"


if __name__ == "__main__":
    sm = SmartMirror(pathlib.Path("config/config.json"))
    sm.mainloop()
