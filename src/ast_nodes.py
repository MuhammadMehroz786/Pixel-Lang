# ast_nodes.py — PixLang Abstract Syntax Tree Node Definitions
# Phase 2 (Syntax Analysis) builds these; Phase 3/4 consume them.
# =============================================================================
 
class Node:
    """Base class for all AST nodes."""
    pass
 
 
# ── Program ───────────────────────────────────────────────────────────────────
 
class Program(Node):
    """Root node: holds a list of statements."""
    def __init__(self, statements):
        self.statements = statements  # List[Node]
 
    def __repr__(self):
        return f"Program({self.statements})"
 
 
# ── Statements ────────────────────────────────────────────────────────────────
 
class CanvasStmt(Node):
    """CANVAS width height"""
    def __init__(self, width, height, line=None):
        self.width  = width   # Expr
        self.height = height  # Expr
        self.line   = line
 
    def __repr__(self):
        return f"CanvasStmt({self.width}, {self.height})"
 
 
class PaletteStmt(Node):
    """PALETTE name: #hex, #hex, ..."""
    def __init__(self, name, colors, line=None):
        self.name   = name    # str
        self.colors = colors  # List[str]  e.g. ["#1A1C2C", ...]
        self.line   = line
 
    def __repr__(self):
        return f"PaletteStmt({self.name}, {self.colors})"
 
 
class FillStmt(Node):
    """FILL color"""
    def __init__(self, color, line=None):
        self.color = color  # Expr (color literal or palette index)
        self.line  = line
 
    def __repr__(self):
        return f"FillStmt({self.color})"
 
 
class VarDecl(Node):
    """VAR name = expr"""
    def __init__(self, name, expr, line=None):
        self.name = name   # str
        self.expr = expr   # Expr
        self.line = line
 
    def __repr__(self):
        return f"VarDecl({self.name}, {self.expr})"
 
 
class AssignStmt(Node):
    """name = expr  (re-assignment)"""
    def __init__(self, name, expr, line=None):
        self.name = name
        self.expr = expr
        self.line = line
 
    def __repr__(self):
        return f"AssignStmt({self.name}, {self.expr})"
 
 
class RectStmt(Node):
    """RECT x, y, w, h, color"""
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
    """CIRCLE cx cy RADIUS r COLOR color"""
    def __init__(self, cx, cy, radius, color, line=None):
        self.cx     = cx
        self.cy     = cy
        self.radius = radius
        self.color  = color
        self.line   = line
 
    def __repr__(self):
        return f"CircleStmt({self.cx},{self.cy},{self.radius},{self.color})"
 
 
class LineStmt(Node):
    """LINE x1 y1 x2 y2 COLOR color"""
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
    """PIXEL x y COLOR color"""
    def __init__(self, x, y, color, line=None):
        self.x     = x
        self.y     = y
        self.color = color
        self.line  = line
 
    def __repr__(self):
        return f"PixelStmt({self.x},{self.y},{self.color})"
 
 
class SaveStmt(Node):
    """SAVE "filename.png" """
    def __init__(self, filename, line=None):
        self.filename = filename  # str
        self.line     = line
 
    def __repr__(self):
        return f"SaveStmt({self.filename})"
 
 
class LoopWhile(Node):
    """LOOP WHILE condition: body ENDLOOP"""
    def __init__(self, condition, body, line=None):
        self.condition = condition  # Expr
        self.body      = body       # List[Node]
        self.line      = line
 
    def __repr__(self):
        return f"LoopWhile({self.condition}, {self.body})"
 
 
class LoopTimes(Node):
    """LOOP TIMES n: body ENDLOOP"""
    def __init__(self, times, body, line=None):
        self.times = times  # Expr
        self.body  = body   # List[Node]
        self.line  = line
 
    def __repr__(self):
        return f"LoopTimes({self.times}, {self.body})"
 
 
class IfStmt(Node):
    """IF condition: then_body [ELSE: else_body] ENDIF"""
    def __init__(self, condition, then_body, else_body=None, line=None):
        self.condition = condition
        self.then_body = then_body  # List[Node]
        self.else_body = else_body  # List[Node] or None
        self.line      = line
 
    def __repr__(self):
        return f"IfStmt({self.condition}, then={self.then_body}, else={self.else_body})"
 
 
# ── Expressions ───────────────────────────────────────────────────────────────
 
class BinOp(Node):
    """Binary operation: left op right"""
    def __init__(self, left, op, right, line=None):
        self.left  = left   # Expr
        self.op    = op     # str  e.g. '+', '-', '*', '/', 'MOD', '>', '<', '==', etc.
        self.right = right  # Expr
        self.line  = line
 
    def __repr__(self):
        return f"BinOp({self.left} {self.op} {self.right})"
 
 
class UnaryOp(Node):
    """Unary operation: op operand"""
    def __init__(self, op, operand, line=None):
        self.op      = op
        self.operand = operand
        self.line    = line
 
    def __repr__(self):
        return f"UnaryOp({self.op}{self.operand})"
 
 
class NumberLit(Node):
    """Integer or float literal."""
    def __init__(self, value, line=None):
        self.value = value  # int or float
        self.line  = line
 
    def __repr__(self):
        return f"Num({self.value})"
 
 
class StringLit(Node):
    """String literal (used in SAVE)."""
    def __init__(self, value, line=None):
        self.value = value  # str without quotes
        self.line  = line
 
    def __repr__(self):
        return f"Str({self.value!r})"
 
 
class ColorLit(Node):
    """Hex color literal like #FF0000."""
    def __init__(self, value, line=None):
        self.value = value  # str e.g. "#FF0000"
        self.line  = line
 
    def __repr__(self):
        return f"Color({self.value})"
 
 
class Identifier(Node):
    """Variable reference."""
    def __init__(self, name, line=None):
        self.name = name
        self.line = line
 
    def __repr__(self):
        return f"Id({self.name})"
 
 
class PaletteIndex(Node):
    """palette_name[index_expr]"""
    def __init__(self, palette_name, index_expr, line=None):
        self.palette_name = palette_name   # str
        self.index_expr   = index_expr     # Expr
        self.line         = line
 
    def __repr__(self):
        return f"PaletteIdx({self.palette_name}[{self.index_expr}])"