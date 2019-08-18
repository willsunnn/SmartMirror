import tkinter
import PathFinder


class LayoutManagerHelper:
    """Class to help manage the widget's dimensions by interfacing with the SmartMirror's LayoutManager"""

    x_dimensions = ["left", "right", "width"]
    y_dimensions = ["top", "bottom", "height"]

    def __init__(self):
        """Creates a LayoutManagerHelper object with no existing constraints"""
        self.setup = True

        self.left = None
        self.right = None
        self.width = None

        self.top = None
        self.bottom = None
        self.height = None

        del self.setup

    def __setattr__(self, key, value):
        """
        Overloads __setattr__ so that when an attribute is set
        it assures that there are only 2 constraints in each dimension
        """
        super.__setattr__(self, key, value)
        if "setup" not in self.__dict__.keys():
            self.assert_no_conflicting_constraints()

    def __getattr__(self, item):
        """
        if the property is defined by a constraint, return the property
        else determine the property based on the object's other properties and return it
        :param item:
        :return:
        """
        value = self.__dict__.get(item, None)
        if value is not None:
            return value
        else:
            (x, y), (width, height) = self.get_rect()
            if item == "left":
                return x
            if item == "right":
                return x + width
            if item == "width":
                return width
            if item == "top":
                return y
            if item == "bottom":
                return y + height
            if item == "height":
                return height

    def assert_no_conflicting_constraints(self):
        """it assures that there are only 2 constraints in each dimension"""
        assert len(list(filter(lambda x: x is not None, map(lambda key: self.__dict__[key], LayoutManagerHelper.x_dimensions)))) <= 2, "There can only be two constraints along the x dimension"
        assert len(list(filter(lambda x: x is not None, map(lambda key: self.__dict__[key], LayoutManagerHelper.y_dimensions)))) <= 2, "There can only be two constraints along the y dimension"

    def get_rect(self) -> ((int, int), (int, int)):
        """
        Generates the rectangle of the widget based on its constraints
        :return: ((leftX, topY), (width, height)) in pixels
        """
        if self.left is None:
            if self.right is None and self.width is None:
                left = 0
            else:
                left = self.right - self.width
        else:
            left = self.left

        if self.right is None and self.width is None:
            width = 100
        elif self.right is None:
            width = self.width
        else:
            width = self.right - left

        if self.top is None:
            top = 0
        else:
            top = self.top

        if self.bottom is None and self.height is None:
            height = 100
        elif self.bottom is None:
            height = self.height
        else:
            height = self.bottom - self.top
        return (left, top), (width, height)


class BaseWidget(tkinter.Frame):
    """
    The Widget that other widgets overwrite
    Makes a uniform protocol for layout and update management
    Methods that should be overwritten:
        update_values
        place
    """
    @classmethod
    def has_necesarry_config(cls):
        """
        Method used to determine if the directory contains the necessary files
        Intended to be used to ensure that auth credentials or file resources exist"""
        return all(map(PathFinder.check_file_exists, cls.get_necesarry_config()))

    @staticmethod
    def get_necesarry_config():
        return []

    def __init__(self, parent, subwidgets=[], constraints=[], props={}):
        """constructs a widget from the config defined by the parameters"""
        tkinter.Frame.__init__(self, parent.get_window())
        self.parent = parent
        self.props = props
        self.id = self.props.get("id", None)
        self.update_time = (lambda val: val if val > 0 else None)(int(self.props.get("update time", -1)))
        self.constraints = constraints
        self.dimensions = LayoutManagerHelper()
        self.subwidgets = list(map(self.parent.construct_widget, subwidgets))
        self.interactable = BaseWidget.prop_get(props, "interactable", False)
        if self.interactable: self.bind("<Button-1>", self.on_click)

    def get_window(self) -> tkinter.Tk:
        """returns the window that the widget is being displayed in"""
        return self.parent.get_window()

    def get_unused_id(self, w) -> str:
        """returns an ID in the widget's layout manager that the widget w can take"""
        return self.parent.get_unused_id(w)

    def get_colors(self) -> {str: str}:
        """returns the dictionary of colors"""
        return self.parent.get_colors()

    def get_color(self, col) -> str:
        return self.get_colors()[col]

    def get_id(self) -> str:
        """if an ID has been defined, returns that ID. If not, it gets a unique ID and saves it, and then returns it"""
        if self.id is None:
            self.id = self.get_unused_id(self)
        return self.id

    def __setattr__(self, key, value):
        """overloads __setattr__ such that if the property is pertinent to layouts,
        that it is handled by the LayoutManagerHelper"""
        if key in LayoutManagerHelper.x_dimensions or key in LayoutManagerHelper.y_dimensions:
            self.dimensions.__setattr__(key, value)
        else:
            super(tkinter.Frame, self).__setattr__(key, value)

    def __getattr__(self, key):
        """overloads __getattr__ such that if the property is pertinent to layouts,
        that it is the value managed by the LayoutManagerHelper"""
        if key in LayoutManagerHelper.x_dimensions or key in LayoutManagerHelper.y_dimensions:
            return self.dimensions.__getattr__(key)
        else:
            return self.__dict__[key]

    def get_rect(self) -> ((int, int), (int, int)):
        """returns the rectangle of the widget managed by LayoutManagerHelper"""
        return self.dimensions.get_rect()

    def get_own_constraints(self) -> [str]:
        """returns the widget's constraints"""
        return self.constraints

    def get_all_constraints(self) -> [str]:
        """returns all the widget's constraints and all its subwidget's constraints"""
        return self.constraints + [constraint for widget in self.subwidgets for constraint in map(lambda w: w.get_all_constraints(), widget)]

    def update_values(self, *args, **kargs) -> ((), {}):
        """
        Updates the values of the widget. The objects returned will be the parameters of the method call the next time the method is called
        :param args:
        :param kargs:
        :return: returns the args, and kargs of the next method call
        """
        kargs.update({"count": kargs.get("count", -1)+1})
        print(f"Widget Updated: id=\"{self.id}\", update #{kargs['count']}")
        return args, kargs

    def place(self, *args, **kargs):
        """Method that can be overwritten to override placement"""
        tkinter.Frame.place(self, *args, **kargs)

    def on_click(self, event):
        """Method that can be called to modify click behavior"""
        print(f"Widget Clicked: id=\"{self.id}\", point=({event.x},{event.y})")

    @staticmethod
    def prop_get(props: {str: str}, prop: str, default, is_acceptable=lambda x: True):
        class PropsException(BaseException):
            pass
        val = props.get(prop, default)
        if is_acceptable(val):
            return val
        else:
            raise PropsException(f"Property of key {prop} from dictionary {props} with default value of {default} is not one of the accepted values {acceptable_values}")
