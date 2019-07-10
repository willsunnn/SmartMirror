import re


class Size:
    pattern = re.compile(r"(\d+(?:\.\d+)?) ?(px|cm|in)")
    units = {"px", "cm", "in"}
    real_units = {"cm", "in"}

    def __init__(self, size_str):
        try:
            size, units = Size.pattern.match(size_str).groups()
            self.num = float(size)
            self.units = units
        except Exception as e:
            e.message = f"Construction of Size object from given size string ({size_str}) has failed:\n" + e.message
            raise

    def __truediv__(self, other):
        if isinstance(other, Size):
            assert any([i in [self.units, other.units] for i in Size.real_units]) and "px" in [self.units, other.units], f"One of the units must be physical and the other must be pixels\n\t{self.units} and {other.units} were given"
            if self.units == "px":
                return Conversion(self, other)
            else:
                return Conversion(other, self)
        return NotImplemented

    def __str__(self):
        return f"{self.num} {self.units}"


class Conversion:
    real_conversions = {
        ("in", "cm"): 2.54,
        ("in", "in"): 1,
        ("cm", "in"): 1/2.54,
        ("cm", "cm"): 1,
    }

    def __init__(self, px_size: Size, real_size: Size):
        assert real_size.units in ["cm", "in"]
        self.conversion = px_size.num / real_size.num
        self.real_units = real_size.units

    def to_px(self, size: Size) -> int:
        if isinstance(size, str):
            size = Size(size)
        if size.units == "px":
            return int(size.num)
        else:
            real_conversion = Conversion.real_conversions[(size.units, self.real_units)]
            return int(size.num * real_conversion * self.conversion)

    def __eq__(self, other):
        if type(other) == Conversion:
            if self.real_units == other.real_units:
                return self.conversion == other.conversion
            else:
                return self.to_px(Size("1in")) == other.to_px(Size("1in"))
        else:
            return NotImplemented

    def __str__(self):
        return f"1 {self.real_units} is {self.conversion} pixels"


class Constraint:
    @staticmethod
    def construct_constraint(layout_manager, description: str):
        left, right = description.split("=")
        obj1, prop1 = left.split(".")
        right = right.split("+")
        assert len(right) <= 2, f"Constraint given (\"{description}\") contains more than one '+' or '-' character on the right side of the equation"
        if len(right) == 1:
            right = right[0]
            if re.match(Size.pattern, right) is not None:
                const = Size(right)
                return Constraint(layout_manager, obj1, prop1, None, None, 1, const)
            else:
                const = Size("0px")
        else:
            const = Size(right[1].strip())
            right = right[0]
        right = right.split("*")
        assert len(right) <= 2, f"Constraint given (\"{description}\") contains more than one '*' character on the right side of the equation"
        if len(right) == 1:
            ratio = 1
            right = right[0]
        else:
            ratio = float(right[0])
            right = right[1]
        obj2, prop2 = right.split(".")

        return Constraint(layout_manager, obj1.strip(), prop1.strip(), obj2.strip(), prop2.strip(), ratio, const)

    def __init__(self, layout_manager, obj1, prop1, obj2=None, prop2=None, ratio=1, const=Size("0px")):
        self.layout_manager = layout_manager
        self.obj1 = obj1
        self.prop1 = prop1
        self.obj2 = obj2
        self.prop2 = prop2
        self.ratio = ratio
        self.const = const

    # Given an identifier, should return a widget
    def get_widget(self, identifier):
        return self.layout_manager.get_widget(identifier)

    def evaluate(self):
        obj1 = self.layout_manager.get_widget(self.obj1)
        if self.obj2 is not None and self.prop2 is not None:
            # obj1.prop1 = obj2.prop2 * ratio + const
            obj2 = self.layout_manager.get_widget(self.obj2)
            return obj1, self.prop1, obj2.__getattr__(self.prop2) * self.ratio + self.layout_manager.to_px(self.const)
        else:
            return obj1, self.prop1, self.layout_manager.to_px(self.const)
