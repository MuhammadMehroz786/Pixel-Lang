from ast_nodes import *


class IRGenerator:
    def __init__(self):
        self.instructions = []
        self._temp_count  = 0
        self._label_count = 0

    def new_temp(self):
        self._temp_count += 1
        return f"t{self._temp_count}"

    def new_label(self):
        self._label_count += 1
        return f"L{self._label_count}"

    def emit(self, *args):
        self.instructions.append(args)

    def generate(self, program: Program):
        for stmt in program.statements:
            self.gen_stmt(stmt)
        return self.instructions

    def gen_stmt(self, node):
        if isinstance(node, CanvasStmt):
            w = self.gen_expr(node.width)
            h = self.gen_expr(node.height)
            self.emit('CANVAS', w, h, None)

        elif isinstance(node, PaletteStmt):
            self.emit('PALETTE', node.name, node.colors, None)

        elif isinstance(node, FillStmt):
            c = self.gen_expr(node.color)
            self.emit('FILL', c, None, None)

        elif isinstance(node, VarDecl):
            val = self.gen_expr(node.expr)
            self.emit('ASSIGN', node.name, val, None)

        elif isinstance(node, AssignStmt):
            val = self.gen_expr(node.expr)
            self.emit('ASSIGN', node.name, val, None)

        elif isinstance(node, RectStmt):
            x = self.gen_expr(node.x)
            y = self.gen_expr(node.y)
            w = self.gen_expr(node.w)
            h = self.gen_expr(node.h)
            c = self.gen_expr(node.color)
            self.emit('RECT', (x, y, w, h, c), None, None)

        elif isinstance(node, CircleStmt):
            cx = self.gen_expr(node.cx)
            cy = self.gen_expr(node.cy)
            r  = self.gen_expr(node.radius)
            c  = self.gen_expr(node.color)
            self.emit('CIRCLE', (cx, cy, r, c), None, None)

        elif isinstance(node, LineStmt):
            x1 = self.gen_expr(node.x1)
            y1 = self.gen_expr(node.y1)
            x2 = self.gen_expr(node.x2)
            y2 = self.gen_expr(node.y2)
            c  = self.gen_expr(node.color)
            self.emit('LINE', (x1, y1, x2, y2, c), None, None)

        elif isinstance(node, PixelStmt):
            x = self.gen_expr(node.x)
            y = self.gen_expr(node.y)
            c = self.gen_expr(node.color)
            self.emit('PIXEL', (x, y, c), None, None)

        elif isinstance(node, SaveStmt):
            self.emit('SAVE', node.filename, None, None)

        elif isinstance(node, LoopWhile):
            start_lbl = self.new_label()
            end_lbl   = self.new_label()
            self.emit('LABEL', start_lbl, None, None)
            cond = self.gen_expr(node.condition)
            self.emit('JUMPF', cond, end_lbl, None)
            for s in node.body:
                self.gen_stmt(s)
            self.emit('JUMP', start_lbl, None, None)
            self.emit('LABEL', end_lbl, None, None)

        elif isinstance(node, LoopTimes):
            counter = self.new_temp()
            limit   = self.gen_expr(node.times)
            self.emit('ASSIGN', counter, 0, None)
            start_lbl = self.new_label()
            end_lbl   = self.new_label()
            self.emit('LABEL', start_lbl, None, None)
            cond_tmp = self.new_temp()
            self.emit('BINOP', cond_tmp, counter, '<', limit)
            self.emit('JUMPF', cond_tmp, end_lbl, None)
            for s in node.body:
                self.gen_stmt(s)
            inc_tmp = self.new_temp()
            self.emit('BINOP', inc_tmp, counter, '+', 1)
            self.emit('ASSIGN', counter, inc_tmp, None)
            self.emit('JUMP', start_lbl, None, None)
            self.emit('LABEL', end_lbl, None, None)

        elif isinstance(node, IfStmt):
            else_lbl = self.new_label()
            end_lbl  = self.new_label()
            cond = self.gen_expr(node.condition)
            self.emit('JUMPF', cond, else_lbl, None)
            for s in node.then_body:
                self.gen_stmt(s)
            self.emit('JUMP', end_lbl, None, None)
            self.emit('LABEL', else_lbl, None, None)
            if node.else_body:
                for s in node.else_body:
                    self.gen_stmt(s)
            self.emit('LABEL', end_lbl, None, None)

    def gen_expr(self, node):
        if isinstance(node, NumberLit):
            return node.value

        if isinstance(node, ColorLit):
            return node.value

        if isinstance(node, StringLit):
            return node.value

        if isinstance(node, Identifier):
            return node.name

        if isinstance(node, PaletteIndex):
            idx = self.gen_expr(node.index_expr)
            tmp = self.new_temp()
            self.emit('PALETTE_IDX', tmp, node.palette_name, idx)
            return tmp

        if isinstance(node, UnaryOp):
            operand = self.gen_expr(node.operand)
            tmp = self.new_temp()
            self.emit('UNARY', tmp, node.op, operand)
            return tmp

        if isinstance(node, BinOp):
            left  = self.gen_expr(node.left)
            right = self.gen_expr(node.right)
            tmp   = self.new_temp()
            self.emit('BINOP', tmp, left, node.op, right)
            return tmp

        raise ValueError(f"Unknown expression node in IR gen: {type(node).__name__}")

    def pretty_print(self):
        lines = []
        for instr in self.instructions:
            op = instr[0]
            if op == 'LABEL':
                lines.append(f"{instr[1]}:")
            elif op == 'ASSIGN':
                lines.append(f"    {instr[1]} = {instr[2]}")
            elif op == 'BINOP':
                lines.append(f"    {instr[1]} = {instr[2]} {instr[3]} {instr[4]}")
            elif op == 'UNARY':
                lines.append(f"    {instr[1]} = {instr[2]}{instr[3]}")
            elif op == 'JUMP':
                lines.append(f"    goto {instr[1]}")
            elif op == 'JUMPF':
                lines.append(f"    if not {instr[1]} goto {instr[2]}")
            elif op == 'CANVAS':
                lines.append(f"    CANVAS {instr[1]} {instr[2]}")
            elif op == 'PALETTE':
                lines.append(f"    PALETTE {instr[1]} {instr[2]}")
            elif op == 'PALETTE_IDX':
                lines.append(f"    {instr[1]} = {instr[2]}[{instr[3]}]")
            elif op == 'FILL':
                lines.append(f"    FILL {instr[1]}")
            elif op == 'RECT':
                x,y,w,h,c = instr[1]
                lines.append(f"    RECT {x},{y},{w},{h},{c}")
            elif op == 'CIRCLE':
                cx,cy,r,c = instr[1]
                lines.append(f"    CIRCLE {cx},{cy} R={r} C={c}")
            elif op == 'LINE':
                x1,y1,x2,y2,c = instr[1]
                lines.append(f"    LINE ({x1},{y1})->({x2},{y2}) C={c}")
            elif op == 'PIXEL':
                x,y,c = instr[1]
                lines.append(f"    PIXEL ({x},{y}) C={c}")
            elif op == 'SAVE':
                lines.append(f"    SAVE \"{instr[1]}\"")
            else:
                lines.append(f"    {instr}")
        return "\n".join(lines)
