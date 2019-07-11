from collections import OrderedDict
import tkinter
import pathlib
from BaseWidget import BaseWidget
from Dimensions import Size, Conversion, Constraint


class LayoutManager:
    """
    Class to manage the layout of individual widgets
    Allows widgets to reference properties of other widgets to allow for dynamic sizing
    """

    #################
    # Setup Methods #
    #################

    def __init__(self, parent, size: {str: tuple}):
        """
        Initializes a layout manager object that manages the widgets of parents.widgets

        :param parent: should be the SmartMirror object that has the property widgets
        :param size: see LayoutManager.set_conversion
        """
        self.widgets: {str: BaseWidget} = parent.widgets
        self.conversion: Conversion = None
        self.physical_size, self.pixel_size = None, None
        self.set_conversion(size)
        self.window = tkinter.Tk()
        self.configure_window()
        self.constraints: [Constraint] = []

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
        self.window.config(background="#000000")
        self.window.geometry(f"{self.conversion.to_px(self.pixel_size[0])}x{self.conversion.to_px(self.pixel_size[1])}")
        self.window.resizable(0, 0)

    ##################
    # Layout Methods #
    ##################

    def add_constraints(self, new_constraints: [str]) -> None:
        """
        Constructs and adds a constraint for each string description in new_constraints
        :param new_constraints: contains strings that follow the format necessary for Constraint.construct_constraint
        """
        self.constraints += map(lambda const: Constraint.construct_constraint(self, const), new_constraints)

    def evaluate_constraints(self) -> None:
        """
        evaluates each constraint's value and sets the corresponding object's property to that value
        constraints are evaluated in the order they are added
        """
        for constraint in self.constraints:
            obj, prop, value = constraint.evaluate()
            obj.__setattr__(prop, value)

    def place_all(self) -> None:
        """positions all the widgets in the window based on their positions defined from the constraints"""
        for widget_id, widget in self.widgets.items():
            (x, y), (width, height) = widget.get_rect()
            widget.place(x=x, y=y, width=width, height=height)

    ##################
    # Helper Methods #
    ##################

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
    def __init__(self, func, window, update_milliseconds: int):
        self.window = window
        self.time = update_milliseconds
        self.func = func

    def __call__(self, *args, **kwargs):
        """calls the function itself, and then schedules the same function call afterwards"""
        self.func(*args, **kwargs)
        self.window.after(self.time, lambda: self.__call__(*args, **kwargs))


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
        LoopMethod(func, self.smart_mirror.get_window(), time)(*args, **kwargs)

    def add_widget_updater(self, widget, update_time) -> None:
        """Specific case of add_update_checker that registers the widget's update_values function"""
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
        self.layout_manager: LayoutManager = LayoutManager(self, config["window_config"])
        self.update_manager: UpdateManager = UpdateManager(self)
        self.add_widgets(map(lambda w: BaseWidget.construct_widget(self, w), config["widgets"]))

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

    def add_widgets(self, widgets: [BaseWidget]) -> None:
        """Adds all the widgets and their corresponding subwidgets, constraints, and update checkers"""
        for widget in widgets:
            self.add_widget(widget)

    def add_widget(self, widget: [BaseWidget]) -> None:
        """Adds a widget and its corresponding subwidgets, constraints, and update checkers"""
        widget_id = widget.get_id()
        assert widget_id not in self.widgets.keys(), f"Error, ID already added\nAddedID = {widget_id}\n" + "Preexisting IDs:\n\t" + "\n\t".join(
            [f"widgets[{widget_id}] = {widget}" for widget_id, widget in self.widgets.items()])
        self.widgets[widget_id] = widget
        self.add_constraints(widget.get_own_constraints())
        self.add_update_checker(widget)
        self.add_widgets(widget.subwidgets)

    def add_constraints(self, constraints: [str]) -> None:
        """Passes the given constraint descriptions to the LayoutManager to be constructed and handled"""
        self.layout_manager.add_constraints(constraints)

    def add_update_checker(self, widget: BaseWidget) -> None:
        """Registers the widget in the UpdateManager so that its value can be updated over time"""
        if widget.get_update_time() is not None:
            self.update_manager.add_widget_updater(widget, widget.get_update_time())

    ####################
    # Protocol Methods #
    ####################

    def get_window(self) -> tkinter.Tk:
        """
        returns the tkinter window that the GUI exists in

        method required by UpdateManager to schedule regular method calls
        method required by BaseWidget as the tkinter frame requires a parent to be constructed within
        """
        return self.layout_manager.window

    def get_unused_id(self, w):
        """
        see LayoutManager.get_unused_id:
            generates an unused ID for a widget in the scenario an ID was not defined in the widget's props
        """
        return self.layout_manager.get_unused_id(w)

    ##################
    # Helper Methods #
    ##################

    @staticmethod
    def parse_json(file_name: pathlib.Path):
        """returns the object constructed from the json file at the given path"""
        import json
        return json.loads(" ".join(open(file_name)))

    def __str__(self):
        """gives details about the SmartMirror's LayoutManager and Widgets"""
        return "\nLayout Manager = " + "\n\t".join(str(self.layout_manager).split("\n")) + "\nWidgets = \n\t" + "\n\t".join(map(lambda t: f"{t[0]}\t:\t{t[1]}", self.widgets.items())) +"\n"


if __name__ == "__main__":
    sm = SmartMirror("config.json")
    print(sm)
    sm.mainloop()
