import re


class Size:
    """
    Objects used to store sizes
    It allows for an easy way to handle multiple units of measurements with the same code
    """
    pattern = re.compile(r"^(\d+(?:\.\d+)?) ?(px|cm|in)$")
    units = {"px", "cm", "in"}
    real_units = {"cm", "in"}

    @staticmethod
    def size_from_str(size_str):
        f"""constructs a Size object from the string if it follows the Size.pattern regular expression ({Size.pattern})"""
        try:
            num, units = Size.pattern.match(size_str).groups()
            return Size(float(num), units)
        except Exception as e:
            e.message = f"Construction of Size object from given size string ({size_str}) has failed:\n" + e.message
            raise

    def __init__(self, num=0.0, units="px"):
        """Constructs a size object"""
        self.num = num
        self.units = units

    def __truediv__(self, other):
        """It returns a Conversion object that is used to convert between two different units of measurement"""
        if isinstance(other, Size):
            assert any([i in [self.units, other.units] for i in Size.real_units]) and "px" in [self.units, other.units], f"One of the units must be physical and the other must be pixels\n\t{self.units} and {other.units} were given"
            if self.units == "px":
                return Conversion(self, other)
            else:
                return Conversion(other, self)
        return NotImplemented

    def __str__(self):
        """Returns the Size's length and units"""
        return f"{self.num} {self.units}"

    def __repr__(self):
        """Returns the Size's representation"""
        return f"Size({self.num},\"{self.units}\""

    def __mul__(self, other):
        """it allows for scaling of a Size object by ints or floats"""
        if isinstance(other, (int, float)):
            return Size(other*self.num, self.units)
        return NotImplemented

    def __rmul__(self, other):
        """it allows for scaling of a Size object by ints or floats"""
        return self * other


class Conversion:
    """This Object is used to convert between physical units (in, cm) and digital units (px) of size"""
    real_conversions = {
        ("in", "cm"): 2.54,
        ("in", "in"): 1,
        ("cm", "in"): 1/2.54,
        ("cm", "cm"): 1,
    }

    def __init__(self, px_size: Size, real_size: Size):
        """Creates a conversion between the two sizes given"""
        assert real_size.units in ["cm", "in"]
        self.conversion = px_size.num / real_size.num
        self.real_units = real_size.units

    def to_px(self, size: Size) -> int:
        """Converts the given size object to a number of pixels"""
        if isinstance(size, str):
            size = Size.size_from_str(size)
        if size.units == "px":
            return int(size.num)
        else:
            real_conversion = Conversion.real_conversions[(size.units, self.real_units)]
            return int(size.num * real_conversion * self.conversion)

    def __eq__(self, other):
        """Checks if two unit conversions are equivalent
        Equivalence is determined by if both conversions return the same pixel num given the same physical Size"""
        if type(other) == Conversion:
            if self.real_units == other.real_units:
                return self.conversion == other.conversion
            else:
                return self.to_px(Size.size_from_str("1in")) == other.to_px(Size.size_from_str("1in"))
        else:
            return NotImplemented

    def __str__(self):
        """Returns the number of pixels one of it's physical units spans"""
        return f"1 {self.real_units} is {self.conversion} pixels"


class Expression:
    """Object used by Constraint to parse and evaluate expressions based on a given string"""
    @staticmethod
    def construct_expressions(expression_strs):
        """returns a list of expressions that when summer together should represent the expression in expression_strs"""
        def split_expressions(strs):
            strs = list(map(lambda s: s.split("-"), strs.split("+")))
            strs = [["+"+l[0].strip()] + list(map(lambda s: "-" + s.strip(), l[1:])) for l in strs]
            return [s for substrs in strs for s in substrs]
        return list(map(Expression.construct_expression, split_expressions(expression_strs)))

    @staticmethod
    def construct_expression(expr):
        """An expression in this case is one term
        This method constructs an expression from the given expr string"""
        og_expr = expr
        try:
            if expr[0] == "-":
                multiplier = -1
                expr = expr[1:]
            else:
                multiplier = 1
                expr = expr[1:]
            if re.match(Size.pattern, expr) is not None:
                return Expression(const=multiplier*Size.size_from_str(expr))
            expr = expr.split("*")
            if len(expr) == 1:
                expr = expr[0]
            else:
                try:
                    multiplier *= float(expr[0])
                    expr = expr[1]
                except ValueError:
                    multiplier *= float(expr[1])
                    expr = expr[0]
            obj, prop = expr.split(".")
            return Expression(obj.strip(), prop.strip(), multiplier)
        except Exception as e:
            raise ValueError(f"Construction of Expression failed: Given expression = \"{og_expr}\"\n{e.args[0]}") from e

    def __init__(self, obj=None, prop=None, multiplier=1, const=Size()):
        """Creates an expression object that represents an algebraic expression
        It can be evaluated to return a value by retrieving the given object's properties"""
        self.obj: str = obj
        self.prop: str = prop
        self.multiplier: float = multiplier
        self.const: Size = const

    def evaluate(self, constraint):
        """
        Returns the number of pixels that this expression represents at the given time of evaluation
        :param constraint: The Expression object is being evaluated based on the constraint object's point of view
                this matters in terms of what the object's parent/self is
        :return: The number of pixels that the expression evaluates to be
        """
        if self.obj is not None and self.prop is not None:
            return self.multiplier * constraint.get_widget(self.obj).__getattr__(self.prop) + constraint.to_px(self.const)
        else:
            return constraint.to_px(self.const)


class Constraint:
    """Used to evaluate all the expressions that determine the object's dimensions"""

    @staticmethod
    def construct_constraint(layout_manager, description: str):
        """Constructs a constraint in the given LayoutManager based on the descriptions string"""
        left, right = description.split("=")
        obj, prop = left.split(".")
        return Constraint(layout_manager, obj.strip(), prop.strip(), Expression.construct_expressions(right))

    def __init__(self, layout_manager, obj, prop, expressions: [Expression]):
        """
        Constructs a Constraint objects
        obj.prop is the property that will be changed
        expressions determines the value of that property at a given time
        """
        self.layout_manager = layout_manager
        self.obj: str = obj
        self.prop: str = prop
        self.expressions: [Expression] = expressions

    def get_widget(self, identifier) -> 'BaseWidget':
        """returns the Widget object that represents the identifier represents"""
        if identifier == "parent":
            return self.layout_manager.get_widget(self.obj).parent
        elif identifier == "self":
            return self.layout_manager.get_widget(self.obj)
        else:
            return self.layout_manager.get_widget(identifier)

    def to_px(self, size: Size) -> int:
        """Is used to determine the px size of a Size object"""
        return self.layout_manager.to_px(size)

    def evaluate(self) -> (('BaseWidget', str), int):
        """returns the obj and prop that will be changed, as well as the value that it will become"""
        return (self.layout_manager.get_widget(self.obj), self.prop), sum(map(lambda exp: exp.evaluate(self), self.expressions))

