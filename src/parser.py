# =============================================================================
# parser.py — PixLang Recursive Descent Parser (Phase 2)
#
# Grammar (EBNF):
#
#   program      → statement* EOF
#   statement    → canvas_stmt | palette_stmt | fill_stmt | var_decl
#                | assign_stmt | rect_stmt | circle_stmt | line_stmt
#                | pixel_stmt | save_stmt | loop_while | loop_times | if_stmt
#                | NEWLINE
#
#   canvas_stmt  → 'CANVAS' expr expr NEWLINE
#   palette_stmt → 'PALETTE' IDENTIFIER ':' COLOR_LIT (',' COLOR_LIT)* NEWLINE
#   fill_stmt    → 'FILL' color_expr NEWLINE
#   var_decl     → 'VAR' IDENTIFIER '=' expr NEWLINE
#   assign_stmt  → IDENTIFIER '=' expr NEWLINE
#   rect_stmt    → 'RECT' expr ',' expr ',' expr ',' expr ',' color_expr NEWLINE
#   circle_stmt  → 'CIRCLE' expr expr 'RADIUS' expr 'COLOR' color_expr NEWLINE
#   line_stmt    → 'LINE' expr expr expr expr 'COLOR' color_expr NEWLINE
#   pixel_stmt   → 'PIXEL' expr expr 'COLOR' color_expr NEWLINE
#   save_stmt    → 'SAVE' STRING NEWLINE
#   loop_while   → 'LOOP' 'WHILE' expr ':' NEWLINE statement* 'ENDLOOP' NEWLINE
#   loop_times   → 'LOOP' 'TIMES' expr ':' NEWLINE statement* 'ENDLOOP' NEWLINE
#   if_stmt      → 'IF' expr ':' NEWLINE statement*
#                  ['ELSE' ':' NEWLINE statement*] 'ENDIF' NEWLINE
#
#   expr         → comparison
#   comparison   → addition (('>'|'<'|'>='|'<='|'=='|'!=') addition)?
#   addition     → term (('+' | '-') term)*
#   term         → factor (('*' | '/' | 'MOD') factor)*
#   factor       → '-' factor | '(' expr ')' | atom
#   atom         → INT | FLOAT | COLOR_LIT | STRING | palette_index | IDENTIFIER
#   color_expr   → COLOR_LIT | palette_index | IDENTIFIER
#   palette_index→ IDENTIFIER '[' expr ']'
# =============================================================================
 
from ast_nodes import *
 
 
class ParseError(Exception):
    def __init__(self, message, token=None):
        loc = f" at Line {token.line}, Col {token.col}" if token else ""
        super().__init__(f"[Parse Error]{loc}: {message}")
        self.token = token
 
 
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos    = 0
 
    # ── Helpers ───────────────────────────────────────────────────────────────
 
    def current(self):
        return self.tokens[self.pos]
 
    def peek(self, offset=1):
        idx = self.pos + offset
        return self.tokens[idx] if idx < len(self.tokens) else self.tokens[-1]
 
    def advance(self):
        tok = self.tokens[self.pos]
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
        return tok
 
    def expect(self, tok_type, value=None):
        tok = self.current()
        if tok.type != tok_type:
            raise ParseError(
                f"Expected {tok_type!r} but got {tok.type!r} ({tok.value!r})", tok
            )
        if value is not None and tok.value != value:
            raise ParseError(
                f"Expected {value!r} but got {tok.value!r}", tok
            )
        return self.advance()
 
    def skip_newlines(self):
        while self.current().type == 'NEWLINE':
            self.advance()
 
    def expect_newline(self):
        """Consume one or more newlines (or EOF)."""
        tok = self.current()
        if tok.type not in ('NEWLINE', 'EOF'):
            raise ParseError(
                f"Expected newline after statement but got {tok.type!r} ({tok.value!r})", tok
            )
        while self.current().type == 'NEWLINE':
            self.advance()
 
    def match_keyword(self, *kws):
        tok = self.current()
        if tok.type == 'KEYWORD' and tok.value in kws:
            return True
        return False
 
    # ── Entry point ───────────────────────────────────────────────────────────
 
    def parse(self):
        self.skip_newlines()
        stmts = []
        while self.current().type != 'EOF':
            if self.current().type == 'NEWLINE':
                self.advance()
                continue
            stmts.append(self.parse_statement())
        return Program(stmts)
 
    # ── Statement dispatcher ──────────────────────────────────────────────────
 
    def parse_statement(self):
        tok = self.current()
        if tok.type == 'KEYWORD':
            kw = tok.value
            if kw == 'CANVAS':   return self.parse_canvas()
            if kw == 'PALETTE':  return self.parse_palette()
            if kw == 'FILL':     return self.parse_fill()
            if kw == 'VAR':      return self.parse_var_decl()
            if kw == 'RECT':     return self.parse_rect()
            if kw == 'CIRCLE':   return self.parse_circle()
            if kw == 'LINE':     return self.parse_line()
            if kw == 'PIXEL':    return self.parse_pixel()
            if kw == 'SAVE':     return self.parse_save()
            if kw == 'LOOP':     return self.parse_loop()
            if kw == 'IF':       return self.parse_if()
            raise ParseError(f"Unexpected keyword {kw!r}", tok)
        elif tok.type == 'IDENTIFIER':
            # Could be assignment: IDENTIFIER '=' expr
            if self.peek().type == 'OP_ASSIGN':
                return self.parse_assign()
            raise ParseError(f"Unexpected identifier {tok.value!r}", tok)
        raise ParseError(f"Unexpected token {tok.type!r} ({tok.value!r})", tok)
 
    # ── Individual statement parsers ──────────────────────────────────────────
 
    def parse_canvas(self):
        line = self.current().line
        self.expect('KEYWORD', 'CANVAS')
        w = self.parse_expr()
        h = self.parse_expr()
        self.expect_newline()
        return CanvasStmt(w, h, line=line)
 
    def parse_palette(self):
        line = self.current().line
        self.expect('KEYWORD', 'PALETTE')
        name_tok = self.expect('IDENTIFIER')
        self.expect('COLON')
        colors = []
        col_tok = self.expect('COLOR_LIT')
        colors.append(col_tok.value)
        while self.current().type == 'COMMA':
            self.advance()
            # allow newline+indent continuation
            self.skip_newlines()
            c = self.expect('COLOR_LIT')
            colors.append(c.value)
        self.expect_newline()
        return PaletteStmt(name_tok.value, colors, line=line)
 
    def parse_fill(self):
        line = self.current().line
        self.expect('KEYWORD', 'FILL')
        color = self.parse_color_expr()
        self.expect_newline()
        return FillStmt(color, line=line)
 
    def parse_var_decl(self):
        line = self.current().line
        self.expect('KEYWORD', 'VAR')
        name_tok = self.expect('IDENTIFIER')
        self.expect('OP_ASSIGN')
        expr = self.parse_expr()
        self.expect_newline()
        return VarDecl(name_tok.value, expr, line=line)
 
    def parse_assign(self):
        line = self.current().line
        name_tok = self.expect('IDENTIFIER')
        self.expect('OP_ASSIGN')
        expr = self.parse_expr()
        self.expect_newline()
        return AssignStmt(name_tok.value, expr, line=line)
 
    def parse_rect(self):
        line = self.current().line
        self.expect('KEYWORD', 'RECT')
        x = self.parse_expr()
        self.expect('COMMA')
        y = self.parse_expr()
        self.expect('COMMA')
        w = self.parse_expr()
        self.expect('COMMA')
        h = self.parse_expr()
        self.expect('COMMA')
        color = self.parse_color_expr()
        self.expect_newline()
        return RectStmt(x, y, w, h, color, line=line)
 
    def parse_circle(self):
        line = self.current().line
        self.expect('KEYWORD', 'CIRCLE')
        cx = self.parse_expr()
        cy = self.parse_expr()
        self.expect('KEYWORD', 'RADIUS')
        r = self.parse_expr()
        self.expect('KEYWORD', 'COLOR')
        color = self.parse_color_expr()
        self.expect_newline()
        return CircleStmt(cx, cy, r, color, line=line)
 
    def parse_line(self):
        line = self.current().line
        self.expect('KEYWORD', 'LINE')
        x1 = self.parse_expr()
        y1 = self.parse_expr()
        x2 = self.parse_expr()
        y2 = self.parse_expr()
        self.expect('KEYWORD', 'COLOR')
        color = self.parse_color_expr()
        self.expect_newline()
        return LineStmt(x1, y1, x2, y2, color, line=line)
 
    def parse_pixel(self):
        line = self.current().line
        self.expect('KEYWORD', 'PIXEL')
        x = self.parse_expr()
        y = self.parse_expr()
        self.expect('KEYWORD', 'COLOR')
        color = self.parse_color_expr()
        self.expect_newline()
        return PixelStmt(x, y, color, line=line)
 
    def parse_save(self):
        line = self.current().line
        self.expect('KEYWORD', 'SAVE')
        fname_tok = self.expect('STRING')
        self.expect_newline()
        return SaveStmt(fname_tok.value, line=line)
 
    def parse_loop(self):
        line = self.current().line
        self.expect('KEYWORD', 'LOOP')
        tok = self.current()
        if tok.type == 'KEYWORD' and tok.value == 'WHILE':
            self.advance()
            cond = self.parse_expr()
            self.expect('COLON')
            self.expect_newline()
            body = self.parse_body('ENDLOOP')
            self.expect('KEYWORD', 'ENDLOOP')
            self.expect_newline()
            return LoopWhile(cond, body, line=line)
        elif tok.type == 'KEYWORD' and tok.value == 'TIMES':
            self.advance()
            n = self.parse_expr()
            self.expect('COLON')
            self.expect_newline()
            body = self.parse_body('ENDLOOP')
            self.expect('KEYWORD', 'ENDLOOP')
            self.expect_newline()
            return LoopTimes(n, body, line=line)
        raise ParseError("Expected WHILE or TIMES after LOOP", tok)
 
    def parse_if(self):
        line = self.current().line
        self.expect('KEYWORD', 'IF')
        cond = self.parse_expr()
        self.expect('COLON')
        self.expect_newline()
        then_body = self.parse_body('ELSE', 'ENDIF')
        else_body = None
        if self.match_keyword('ELSE'):
            self.advance()
            self.expect('COLON')
            self.expect_newline()
            else_body = self.parse_body('ENDIF')
        self.expect('KEYWORD', 'ENDIF')
        self.expect_newline()
        return IfStmt(cond, then_body, else_body, line=line)
 
    def parse_body(self, *terminators):
        """Parse statements until we hit one of the terminator keywords."""
        stmts = []
        while True:
            self.skip_newlines()
            tok = self.current()
            if tok.type == 'EOF':
                break
            if tok.type == 'KEYWORD' and tok.value in terminators:
                break
            stmts.append(self.parse_statement())
        return stmts
 
    # ── Color expression ──────────────────────────────────────────────────────
 
    def parse_color_expr(self):
        tok = self.current()
        if tok.type == 'COLOR_LIT':
            self.advance()
            return ColorLit(tok.value, line=tok.line)
        # palette_index or bare identifier
        if tok.type == 'IDENTIFIER':
            if self.peek().type == 'LBRACKET':
                return self.parse_palette_index()
            self.advance()
            return Identifier(tok.value, line=tok.line)
        raise ParseError(f"Expected a color value but got {tok.type!r}", tok)
 
    def parse_palette_index(self):
        tok = self.current()
        name = self.advance().value   # IDENTIFIER
        self.expect('LBRACKET')
        idx = self.parse_expr()
        self.expect('RBRACKET')
        return PaletteIndex(name, idx, line=tok.line)
 
    # ── Expression grammar (recursive descent) ────────────────────────────────
 
    def parse_expr(self):
        return self.parse_comparison()
 
    def parse_comparison(self):
        left = self.parse_addition()
        cmp_ops = {
            'OP_LT': '<', 'OP_GT': '>', 'OP_LEQ': '<=',
            'OP_GEQ': '>=', 'OP_EQ': '==', 'OP_NEQ': '!=',
        }
        tok = self.current()
        if tok.type in cmp_ops:
            op = cmp_ops[tok.type]
            line = tok.line
            self.advance()
            right = self.parse_addition()
            return BinOp(left, op, right, line=line)
        return left
 
    def parse_addition(self):
        left = self.parse_term()
        while self.current().type in ('OP_PLUS', 'OP_MINUS'):
            op  = '+' if self.current().type == 'OP_PLUS' else '-'
            line = self.current().line
            self.advance()
            right = self.parse_term()
            left  = BinOp(left, op, right, line=line)
        return left
 
    def parse_term(self):
        left = self.parse_factor()
        while self.current().type in ('OP_MUL', 'OP_DIV') or (
            self.current().type == 'KEYWORD' and self.current().value == 'MOD'
        ):
            tok = self.current()
            if tok.type == 'OP_MUL':     op = '*'
            elif tok.type == 'OP_DIV':   op = '/'
            else:                         op = 'MOD'
            line = tok.line
            self.advance()
            right = self.parse_factor()
            left  = BinOp(left, op, right, line=line)
        return left
 
    def parse_factor(self):
        tok = self.current()
        # Unary minus
        if tok.type == 'OP_MINUS':
            self.advance()
            operand = self.parse_factor()
            return UnaryOp('-', operand, line=tok.line)
        # Grouped expression
        if tok.type == 'LPAREN':
            self.advance()
            expr = self.parse_expr()
            self.expect('RPAREN')
            return expr
        return self.parse_atom()
 
    def parse_atom(self):
        tok = self.current()
        if tok.type == 'INT':
            self.advance()
            return NumberLit(tok.value, line=tok.line)
        if tok.type == 'FLOAT':
            self.advance()
            return NumberLit(tok.value, line=tok.line)
        if tok.type == 'COLOR_LIT':
            self.advance()
            return ColorLit(tok.value, line=tok.line)
        if tok.type == 'STRING':
            self.advance()
            return StringLit(tok.value, line=tok.line)
        if tok.type == 'IDENTIFIER':
            # palette_index or variable
            if self.peek().type == 'LBRACKET':
                return self.parse_palette_index()
            self.advance()
            return Identifier(tok.value, line=tok.line)
        raise ParseError(
            f"Unexpected token in expression: {tok.type!r} ({tok.value!r})", tok
        )