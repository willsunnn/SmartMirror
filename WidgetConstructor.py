def construct_widgets(json, parent_frame):
    widgets = []
    for widget_definition in json:
        widgets.append(construct_widget(widget_definition, parent_frame))
    return widgets


def construct_widget(widget_definition, parent_frame):
    #widget_type = widget_name_to_class[widget_definition["name"]]
    #props = widget_definition["props"]
    #rect = widget_definition["rect"]
    #return widget_type(parent_frame, rect, props)
    pass
