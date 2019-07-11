import tkinter


class LayoutManagerHelper:
    x_dimensions = ["left", "right", "width"]
    y_dimensions = ["top", "bottom", "height"]

    def __init__(self):
        self.setup = True

        self.left = None
        self.right = None
        self.width = None

        self.top = None
        self.bottom = None
        self.height = None

        self.setup = False

    def __setattr__(self, key, value):
        self.__dict__[key] = value
        if not self.setup:
            self.assert_no_conflicting_constraints()

    def __getattr__(self, item):
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
        assert len(list(filter(lambda x: x is not None, map(lambda key: self.__dict__[key], LayoutManagerHelper.x_dimensions)))) <= 2, "There can only be two constraints along the x dimension"
        assert len(list(filter(lambda x: x is not None, map(lambda key: self.__dict__[key], LayoutManagerHelper.y_dimensions)))) <= 2, "There can only be two constraints along the y dimension"

    def get_rect(self) -> ((int, int), (int, int)):
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
    @staticmethod
    def construct_widget(parent, widget_config):
        if "subwidgets" not in widget_config:
            widget_config["subwidgets"] = []
        return BaseWidget(parent, widget_config["subwidgets"], widget_config["constraints"], widget_config["props"])

    def __init__(self, parent, subwidgets=[], constraints=[], props={}):
        tkinter.Frame.__init__(self, parent.get_window())
        self.parent = parent
        self.props = props
        if "id" in self.props:
            self.id = self.props["id"]
        else:
            self.id = None
        self.constraints = constraints
        self.dimensions = LayoutManagerHelper()
        self.subwidgets = list(map(lambda w: BaseWidget.construct_widget(self, w), subwidgets))

    def get_window(self):
        return self.parent.get_window()

    def get_unused_id(self, w):
        return self.parent.get_unused_id(w)

    def get_id(self) -> str:
        if self.id is None:
            self.id = self.get_unused_id(self)
        return self.id

    def __setattr__(self, key, value):
        if key in LayoutManagerHelper.x_dimensions or key in LayoutManagerHelper.y_dimensions:
            self.dimensions.__setattr__(key, value)
        else:
            super(tkinter.Frame, self).__setattr__(key, value)

    def __getattr__(self, key):
        if key in LayoutManagerHelper.x_dimensions or key in LayoutManagerHelper.y_dimensions:
            return self.dimensions.__getattr__(key)
        else:
            return self.__dict__[key]

    def get_rect(self) -> ((int, int), (int, int)):
        return self.dimensions.get_rect()

    def get_update_time(self):
        if "update time" in self.props:
            return int(self.props["update time"])

    def get_own_constraints(self) -> [str]:
        return self.constraints

    def get_all_constraints(self) -> [str]:
        return self.constraints + [constraint for constrList in map(lambda x: x.constraints, self.subwidgets) for constraint in constrList]

    def update_values(self):
        import datetime
        print(f"Widget Updated: id:{self.id} updated at time {datetime.datetime.now()}")

