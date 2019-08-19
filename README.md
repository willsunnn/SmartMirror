# SmartMirror
**Python TKinter based GUI for Smart Mirror**

## Config Setup

* Go to [config.json](./config/config.json) to change layout of widgets or add widgets
* Move widgets by changing their constraints
* Tweak widgets by adjusting their properties in the **props** section of each widget definition of the [config file](./config/config.json)

### BaseWidget Properties
Property Name | Default Value | Acceptable Values| Description
--- | --- |--- | ---
id | - |- |id is used in constraint definitions. If none is given, the system will give the widget a unique ID
update time | None | positive int | time in milliseconds between updates. No updates if value is None
interactable | false| true/false | If true, widget will run on_click function when clicked

### ClockWidget Properties
Property Name | Default Value | Acceptable Values| Description
--- | --- |--- | ---
clock type | analog | analog / digital | changes the way the clock is displayed

### CalendarWidget Properties
Property Name | Default Value | Acceptable Values| Description
--- | --- |--- | ---
num events | 10 | positive int | changes the number of events to display
end date | today + 2 additional days | date | filters events to only show events before the end date
calendar whitelist | [] | list of strings | whitelists calendars whose names matches any of those in the property. If whitelist is non-empty, blacklist property is ignored
calendar blacklist | [] | list of strings | blacklists calendars whose names matches any of those in the property
display fields | [] | list of fields | changes which fields (and what order) the widget should display


### Adding Custom Widgets

1. Go to [AddonWidgets folder](./Widgets/AddonWidgets)
2. Create a folder containing a python module of the same name, with a class of that name

For example:
⋅⋅* If I am making a Widget called **BirthdayWidget**
⋅I will have a directory /Widgets/AddonWidgets/BirthdayWidget
This directory will contain the BirthdayWidget.py module
This module defines the BirthdayWidget class


### Setting up CalendarWidget

See instructions in [GoogleCalendarAPI/setup.md](./config/GoogleCalendarAPI/setup.md)

## Development Guide

**Examples can be found in Widgets folder**

1. See **Adding Custom Widgets**
2. import BaseWidget from Widgets/BaseWidget
3. Methods to overload:
* **\_\_init\_\_**: change how the widget is initialized. Add subwidgets or tkinter Frames
* **update_values**: a function called to update the data stored in the widget itself. It is updated based on the "*update time*" property in the config file
* **place**: Method that can be overwritten to override widget placement
* **on_click**: Method that is called when the widget is clicked. Property "interactable" needs to be true in config, or manually changed in \_\_init\_\_
* **get_necessary_config**: When called, should return a list of path strings (relative to project root directory) that are necesarry for the widget's operation
