from tkinter import Label
from Widgets.BaseWidget import BaseWidget
from PIL import ImageTk, Image
import datetime


class ClockWidget(BaseWidget):
    def __init__(self, parent, subwidgets=[], constraints=[], props={}):
        BaseWidget.__init__(self, parent, subwidgets, constraints, props)
        self.type = ClockWidget.prop_get(props, "clock type", "analog", lambda x: x in ["digital", "analog"])
        self.config(bg=self.get_bg())
        self.clock_dimensions = (0, 0)
        self.hour, self.minute, self.seconds = 0, 0, 0
        self.update_values()
        self.clock_label = Label(self, bg=self.get_bg())

    def place(self, *args, **kargs):
        self.update_dimensions()
        BaseWidget.place(self, *args, **kargs)
        if self.type == "analog":
            self.update_dimensions()
            self.draw_analog()
        else:
            self.draw_digital()
        
    def draw_analog(self):
        back = Image.open("assets/clock_widget/back.png").resize(self.clock_dimensions, Image.ANTIALIAS).convert("RGBA")
        hours = Image.open("assets/clock_widget/hours.png").resize(self.clock_dimensions, Image.ANTIALIAS).rotate(-0.5*(self.hour*60+self.minute)).convert("RGBA")
        minutes = Image.open("assets/clock_widget/minutes.png").resize(self.clock_dimensions, Image.ANTIALIAS).rotate(-6*self.minute).convert("RGBA")
        back.paste(hours, (0,0), hours)
        back.paste(minutes, (0,0), minutes)
        self.clock_label.photo_ref = ImageTk.PhotoImage(back)
        self.clock_label.config(image=self.clock_label.photo_ref)
        self.clock_label.pack()

    def draw_digital(self):
        pass

    def update_dimensions(self):
        if self.type == "analog":
            diameter = min(self.width, self.height)
            self.clock_dimensions = (diameter, diameter)
        else:
            self.clock_dimensions = (self.width, self.height)

    def update_values(self):
        now = datetime.datetime.now()
        self.hour, self.minute, self.seconds = now.hour, now.minute, now.second
