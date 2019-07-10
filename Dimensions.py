import re
import cProfile


class Size:
    pattern = re.compile(r"^(\d+(?:\.\d+)?) ?(px|cm|in)$")
    units = {"px", "cm", "in"}
    real_units = {"cm", "in"}

    @staticmethod
    def size_from_str(size_str):
        try:
            num, units = Size.pattern.match(size_str).groups()
            return Size(float(num), units)
        except Exception as e:
            e.message = f"Construction of Size object from given size string ({size_str}) has failed:\n" + e.message
            raise

    def __init__(self, num=0.0, units="px"):
        self.num = num
        self.units = units

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

    def __repr__(self):
        return f"Size({self.num},\"{self.units}\""

    def __mul__(self, other):
        if isinstance(other, (int, float)):
            return Size(other*self.num, self.units)
        return NotImplemented

    def __rmul__(self, other):
        return self * other


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
            size = Size.size_from_str(size)
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
                return self.to_px(Size.size_from_str("1in")) == other.to_px(Size.size_from_str("1in"))
        else:
            return NotImplemented

    def __str__(self):
        return f"1 {self.real_units} is {self.conversion} pixels"


class Expression:
    @staticmethod
    def construct_expressions(expression_strs):
        def split_expressions(strs):
            strs = list(map(lambda s: s.split("-"), strs.split("+")))
            strs = [["+"+l[0].strip()] + list(map(lambda s: "-" + s.strip(), l[1:])) for l in strs]
            return [s for substrs in strs for s in substrs]
        return list(map(Expression.construct_expression, split_expressions(expression_strs)))

    @staticmethod
    def construct_expression(expr):
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
        self.obj: str = obj
        self.prop: str = prop
        self.multiplier: float = multiplier
        self.const: Size = const

    def evaluate(self, constraint):
        if self.obj is not None and self.prop is not None:
            return self.multiplier * constraint.get_widget(self.obj).__getattr__(self.prop) + constraint.to_px(self.const)
        else:
            return constraint.to_px(self.const)


class Constraint:
    @staticmethod
    def construct_constraint(layout_manager, description: str):
        left, right = description.split("=")
        obj, prop = left.split(".")
        expressions = Expression.construct_expressions(right)
        return Constraint(layout_manager, obj.strip(), prop.strip(), expressions)

    def __init__(self, layout_manager, obj, prop, expressions: [Expression]):
        self.layout_manager = layout_manager
        self.obj: str = obj
        self.prop: str = prop
        self.expressions: [Expression] = expressions

    def get_widget(self, identifier):
        if identifier == "parent":
            return self.layout_manager.get_widget(self.obj).parent
        return self.layout_manager.get_widget(identifier)

    def to_px(self, size: Size):
        return self.layout_manager.to_px(size)

    def evaluate(self):
        val = 0
        for expression in self.expressions:
            val += expression.evaluate(self)
        return self.layout_manager.get_widget(self.obj), self.prop, val

