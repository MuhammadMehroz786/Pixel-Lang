class Node:
    pass


class Program(Node):
    def __init__(self, statements):
        self.statements = statements

    def __repr__(self):
        return f"Program({self.statements})"


class CanvasStmt(Node):
    def __init__(self, width, height, line=None):
        self.width  = width
        self.height = height
        self.line   = line

    def __repr__(self):
        return f"CanvasStmt({self.width}, {self.height})"


class PaletteStmt(Node):
    def __init__(self, name, colors, line=None):
        self.name   = name
        self.colors = colors
        self.line   = line

    def __repr__(self):
        return f"PaletteStmt({self.name}, {self.colors})"


class FillStmt(Node):
    def __init__(self, color, line=None):
        self.color = color
        self.line  = line

    def __repr__(self):
        return f"FillStmt({self.color})"


class VarDecl(Node):
    def __init__(self, name, expr, line=None):
        self.name = name
        self.expr = expr
        self.line = line

    def __repr__(self):
        return f"VarDecl({self.name}, {self.expr})"


class AssignStmt(Node):
    def __init__(self, name, expr, line=None):
        self.name = name
        self.expr = expr
        self.line = line

    def __repr__(self):
        return f"AssignStmt({self.name}, {self.expr})"


class RectStmt(Node):
    def __init__(self, x, y, w, h, color, line=None):
        self.x     = x
        self.y     = y
        self.w     = w
        self.h     = h
        self.color = color
        self.line  = line

    def __repr__(self):
        return f"RectStmt({self.x},{self.y},{self.w},{self.h},{self.color})"


class CircleStmt(Node):
    def __init__(self, cx, cy, radius, color, line=None):
        self.cx     = cx
        self.cy     = cy
        self.radius = radius
        self.color  = color
        self.line   = line

    def __repr__(self):
        return f"CircleStmt({self.cx},{self.cy},{self.radius},{self.color})"


class LineStmt(Node):
    def __init__(self, x1, y1, x2, y2, color, line=None):
        self.x1    = x1
        self.y1    = y1
        self.x2    = x2
        self.y2    = y2
        self.color = color
        self.line  = line

    def __repr__(self):
        return f"LineStmt({self.x1},{self.y1},{self.x2},{self.y2},{self.color})"


class PixelStmt(Node):
    def __init__(self, x, y, color, line=None):
        self.x     = x
        self.y     = y
        self.color = color
        self.line  = line

    def __repr__(self):
        return f"PixelStmt({self.x},{self.y},{self.color})"


class SaveStmt(Node):
    def __init__(self, filename, line=None):
        self.filename = filename
        self.line     = line

    def __repr__(self):
        return f"SaveStmt({self.filename})"


class LoopWhile(Node):
    def __init__(self, condition, body, line=None):
        self.condition = condition
        self.body      = body
        self.line      = line

    def __repr__(self):
        return f"LoopWhile({self.condition}, {self.body})"


class LoopTimes(Node):
    def __init__(self, times, body, line=None):
        self.times = times
        self.body  = body
        self.line  = line

    def __repr__(self):
        return f"LoopTimes({self.times}, {self.body})"


class IfStmt(Node):
    def __init__(self, condition, then_body, else_body=None, line=None):
        self.condition = condition
        self.then_body = then_body
        self.else_body = else_body
        self.line      = line

    def __repr__(self):
        return f"IfStmt({self.condition}, then={self.then_body}, else={self.else_body})"


class BinOp(Node):
    def __init__(self, left, op, right, line=None):
        self.left  = left
        self.op    = op
        self.right = right
        self.line  = line

    def __repr__(self):
        return f"BinOp({self.left} {self.op} {self.right})"


class UnaryOp(Node):
    def __init__(self, op, operand, line=None):
        self.op      = op
        self.operand = operand
        self.line    = line

    def __repr__(self):
        return f"UnaryOp({self.op}{self.operand})"


class NumberLit(Node):
    def __init__(self, value, line=None):
        self.value = value
        self.line  = line

    def __repr__(self):
        return f"Num({self.value})"


class StringLit(Node):
    def __init__(self, value, line=None):
        self.value = value
        self.line  = line

    def __repr__(self):
        return f"Str({self.value!r})"


class ColorLit(Node):
    def __init__(self, value, line=None):
        self.value = value
        self.line  = line

    def __repr__(self):
        return f"Color({self.value})"


class Identifier(Node):
    def __init__(self, name, line=None):
        self.name = name
        self.line = line

    def __repr__(self):
        return f"Id({self.name})"


class PaletteIndex(Node):
    def __init__(self, palette_name, index_expr, line=None):
        self.palette_name = palette_name
        self.index_expr   = index_expr
        self.line         = line

    def __repr__(self):
        return f"PaletteIdx({self.palette_name}[{self.index_expr}])"
