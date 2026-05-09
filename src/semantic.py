# =============================================================================
# semantic.py — PixLang Semantic Analyzer (Phase 3)
#
# Responsibilities:
#   1. Build and manage a symbol table with scope support
#   2. Resolve variable references (undefined variable detection)
#   3. Type-check expressions (INT, FLOAT, COLOR, STRING)
#   4. Validate palette references (palette must be declared before use)
#   5. Validate CANVAS is declared before drawing commands
#   6. Annotate AST nodes with resolved types
#
# Symbol Table Structure (per scope level):
#   {
#     'name': { 'kind': 'VAR'|'PALETTE', 'type': 'INT'|'FLOAT'|'COLOR'|'STRING', 'line': N }
#   }
# =============================================================================
 
from ast_nodes import *
 
 
class SemanticError(Exception):
    def __init__(self, message, line=None):
        loc = f" at Line {line}" if line else ""
        super().__init__(f"[Semantic Error]{loc}: {message}")
        self.line = line
 
 
# ── Symbol Table ──────────────────────────────────────────────────────────────
 
class SymbolTable:
    """
    Scoped symbol table.  Each scope is a dict.
    Scopes are pushed/popped as we enter/exit loops and conditionals.
    """
    def __init__(self):
        self.scopes = [{}]   # stack of dicts; index 0 = global
 
    def push_scope(self):
        self.scopes.append({})
 
    def pop_scope(self):
        if len(self.scopes) > 1:
            self.scopes.pop()
 
    def declare(self, name, kind, type_, line=None):
        """Declare in the current (innermost) scope."""
        self.scopes[-1][name] = {'kind': kind, 'type': type_, 'line': line}
 
    def lookup(self, name):
        """Walk scopes from innermost to outermost."""
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None
 
    def dump(self):
        """Return a human-readable dump for --debug output."""
        lines = []
        for depth, scope in enumerate(self.scopes):
            lines.append(f"  Scope {depth} ({'global' if depth == 0 else 'local'}):")
            for name, info in scope.items():
                lines.append(f"    {name:20s} kind={info['kind']:8s} type={info['type']}")
        return "\n".join(lines)
 
 
# ── Semantic Analyzer ─────────────────────────────────────────────────────────
 
class SemanticAnalyzer:
    def __init__(self):
        self.sym    = SymbolTable()
        self.canvas_declared = False
        self.palettes = {}   # palette_name → list of colors
 
    # ── Entry point ───────────────────────────────────────────────────────────
 
    def analyze(self, program: Program):
        for stmt in program.statements:
            self.check_stmt(stmt)
        return self.sym
 
    # ── Statement checking ────────────────────────────────────────────────────
 
    def check_stmt(self, node):
        if isinstance(node, CanvasStmt):
            self._check_numeric_expr(node.width)
            self._check_numeric_expr(node.height)
            self.canvas_declared = True
 
        elif isinstance(node, PaletteStmt):
            self.palettes[node.name] = node.colors
            self.sym.declare(node.name, 'PALETTE', 'PALETTE', line=node.line)
 
        elif isinstance(node, FillStmt):
            self._require_canvas(node.line)
            self.check_color_expr(node.color, node.line)
 
        elif isinstance(node, VarDecl):
            t = self.check_expr(node.expr)
            self.sym.declare(node.name, 'VAR', t, line=node.line)
 
        elif isinstance(node, AssignStmt):
            sym = self.sym.lookup(node.name)
            if sym is None:
                raise SemanticError(
                    f"Assignment to undeclared variable '{node.name}'", node.line
                )
            t = self.check_expr(node.expr)
            # allow INT/FLOAT interop
            if not self._types_compatible(sym['type'], t):
                raise SemanticError(
                    f"Type mismatch: variable '{node.name}' is {sym['type']} "
                    f"but assigned {t}", node.line
                )
 
        elif isinstance(node, RectStmt):
            self._require_canvas(node.line)
            self._check_numeric_expr(node.x)
            self._check_numeric_expr(node.y)
            self._check_numeric_expr(node.w)
            self._check_numeric_expr(node.h)
            self.check_color_expr(node.color, node.line)
 
        elif isinstance(node, CircleStmt):
            self._require_canvas(node.line)
            self._check_numeric_expr(node.cx)
            self._check_numeric_expr(node.cy)
            self._check_numeric_expr(node.radius)
            self.check_color_expr(node.color, node.line)
 
        elif isinstance(node, LineStmt):
            self._require_canvas(node.line)
            for e in (node.x1, node.y1, node.x2, node.y2):
                self._check_numeric_expr(e)
            self.check_color_expr(node.color, node.line)
 
        elif isinstance(node, PixelStmt):
            self._require_canvas(node.line)
            self._check_numeric_expr(node.x)
            self._check_numeric_expr(node.y)
            self.check_color_expr(node.color, node.line)
 
        elif isinstance(node, SaveStmt):
            if not node.filename.endswith('.png'):
                raise SemanticError(
                    f"SAVE filename must end with .png, got '{node.filename}'",
                    node.line
                )
 
        elif isinstance(node, LoopWhile):
            self._check_bool_expr(node.condition, node.line)
            self.sym.push_scope()
            for s in node.body:
                self.check_stmt(s)
            self.sym.pop_scope()
 
        elif isinstance(node, LoopTimes):
            self._check_numeric_expr(node.times)
            self.sym.push_scope()
            for s in node.body:
                self.check_stmt(s)
            self.sym.pop_scope()
 
        elif isinstance(node, IfStmt):
            self._check_bool_expr(node.condition, node.line)
            self.sym.push_scope()
            for s in node.then_body:
                self.check_stmt(s)
            self.sym.pop_scope()
            if node.else_body:
                self.sym.push_scope()
                for s in node.else_body:
                    self.check_stmt(s)
                self.sym.pop_scope()
 
    # ── Expression type inference ─────────────────────────────────────────────
 
    def check_expr(self, node) -> str:
        """Return the type string of an expression node."""
        if isinstance(node, NumberLit):
            return 'FLOAT' if isinstance(node.value, float) else 'INT'
 
        if isinstance(node, ColorLit):
            return 'COLOR'
 
        if isinstance(node, StringLit):
            return 'STRING'
 
        if isinstance(node, Identifier):
            sym = self.sym.lookup(node.name)
            if sym is None:
                raise SemanticError(
                    f"Undefined variable '{node.name}'", node.line
                )
            return sym['type']
 
        if isinstance(node, PaletteIndex):
            if node.palette_name not in self.palettes:
                raise SemanticError(
                    f"Undefined palette '{node.palette_name}'", node.line
                )
            self._check_numeric_expr(node.index_expr)
            return 'COLOR'
 
        if isinstance(node, UnaryOp):
            t = self.check_expr(node.operand)
            if t not in ('INT', 'FLOAT'):
                raise SemanticError(
                    f"Unary '-' requires numeric operand, got {t}", node.line
                )
            return t
 
        if isinstance(node, BinOp):
            lt = self.check_expr(node.left)
            rt = self.check_expr(node.right)
            # Comparison operators → boolean-ish (represented as INT)
            if node.op in ('<', '>', '<=', '>=', '==', '!='):
                if not (self._types_compatible(lt, rt)):
                    raise SemanticError(
                        f"Comparison between incompatible types {lt} and {rt}",
                        node.line
                    )
                return 'INT'
            # MOD only on INT
            if node.op == 'MOD':
                if lt != 'INT' or rt != 'INT':
                    raise SemanticError(
                        f"MOD requires INT operands, got {lt} and {rt}", node.line
                    )
                return 'INT'
            # Arithmetic
            if lt not in ('INT', 'FLOAT') or rt not in ('INT', 'FLOAT'):
                raise SemanticError(
                    f"Arithmetic on non-numeric types {lt} and {rt}", node.line
                )
            return 'FLOAT' if 'FLOAT' in (lt, rt) else 'INT'
 
        raise SemanticError(f"Unknown expression node: {type(node).__name__}")
 
    def check_color_expr(self, node, line):
        t = self.check_expr(node)
        if t != 'COLOR':
            raise SemanticError(f"Expected COLOR but got {t}", line)
 
    # ── Internal helpers ──────────────────────────────────────────────────────
 
    def _check_numeric_expr(self, node):
        t = self.check_expr(node)
        if t not in ('INT', 'FLOAT'):
            raise SemanticError(
                f"Expected numeric expression but got {t}",
                getattr(node, 'line', None)
            )
 
    def _check_bool_expr(self, node, line):
        """Conditions should be comparison or numeric (non-zero = true)."""
        t = self.check_expr(node)
        if t not in ('INT', 'FLOAT'):
            raise SemanticError(
                f"Condition must be numeric/boolean expression, got {t}", line
            )
 
    def _require_canvas(self, line):
        if not self.canvas_declared:
            raise SemanticError(
                "Drawing command used before CANVAS declaration", line
            )
 
    def _types_compatible(self, t1, t2):
        numeric = {'INT', 'FLOAT'}
        if t1 in numeric and t2 in numeric:
            return True
        return t1 == t2