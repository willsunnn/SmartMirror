from BaseWidget import BaseWidget


class TextWidget(BaseWidget):
    @staticmethod
    def construct_widget(parent, widget_config):
        """constructs a widget from the widget config json"""
        if "subwidgets" not in widget_config:
            widget_config["subwidgets"] = []
        return TextWidget(parent, widget_config["subwidgets"], widget_config["constraints"], widget_config["props"])

    def __init__(self, parent, subwidgets=[], constraints=[], props={}):
        BaseWidget.__init__(self, parent, subwidgets, constraints, props)
