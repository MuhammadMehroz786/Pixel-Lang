# =============================================================================
# lexer.py — PixLang Lexical Analyzer (Phase 1)
#
# Converts raw source text into a stream of Token objects.
# Uses hand-written DFA logic (equivalent to the state diagram in the docs).
#
# Token categories (regex-equivalent rules):
#   KEYWORD    : CANVAS|PALETTE|FILL|VAR|LOOP|WHILE|TIMES|ENDLOOP|
#                IF|ELSE|ENDIF|RECT|CIRCLE|LINE|PIXEL|SAVE|
#                RADIUS|COLOR|MOD
#   IDENTIFIER : [A-Za-z_][A-Za-z0-9_]*
#   INT        : [0-9]+
#   FLOAT      : [0-9]+ '.' [0-9]+
#   COLOR_LIT  : '#' [0-9A-Fa-f]{3,6}
#   STRING     : '"' [^"]* '"'
#   COMMENT    : ';' ... <end of line>   → skipped
#   OPERATORS  : + - * / ( ) [ ] , : = < > <= >= == !=
#   NEWLINE    : '\n'
# =============================================================================
 
import re
 
# ── Token definition ──────────────────────────────────────────────────────────
 
class Token:
    __slots__ = ('type', 'value', 'line', 'col')
 
    def __init__(self, type_, value, line, col):
        self.type  = type_   # str
        self.value = value   # str | int | float
        self.line  = line
        self.col   = col
 
    def __repr__(self):
        return f"Token({self.type}, {self.value!r}, L{self.line}:C{self.col})"
 
 
# ── Keyword set ───────────────────────────────────────────────────────────────
 
KEYWORDS = {
    'CANVAS', 'PALETTE', 'FILL', 'VAR', 'LOOP', 'WHILE', 'TIMES',
    'ENDLOOP', 'IF', 'ELSE', 'ENDIF', 'RECT', 'CIRCLE', 'LINE',
    'PIXEL', 'SAVE', 'RADIUS', 'COLOR', 'MOD',
}
 
# ── Token specification as ordered list of (type, compiled_regex) ─────────────
 
TOKEN_SPEC = [
    ('FLOAT',       re.compile(r'\d+\.\d+')),
    ('INT',         re.compile(r'\d+')),
    ('COLOR_LIT',   re.compile(r'#[0-9A-Fa-f]{3,6}')),
    ('STRING',      re.compile(r'"[^"]*"')),
    ('OP_LEQ',      re.compile(r'<=')),
    ('OP_GEQ',      re.compile(r'>=')),
    ('OP_EQ',       re.compile(r'==')),
    ('OP_NEQ',      re.compile(r'!=')),
    ('OP_LT',       re.compile(r'<')),
    ('OP_GT',       re.compile(r'>')),
    ('OP_ASSIGN',   re.compile(r'=')),
    ('OP_PLUS',     re.compile(r'\+')),
    ('OP_MINUS',    re.compile(r'-')),
    ('OP_MUL',      re.compile(r'\*')),
    ('OP_DIV',      re.compile(r'/')),
    ('LPAREN',      re.compile(r'\(')),
    ('RPAREN',      re.compile(r'\)')),
    ('LBRACKET',    re.compile(r'\[')),
    ('RBRACKET',    re.compile(r'\]')),
    ('COMMA',       re.compile(r',')),
    ('COLON',       re.compile(r':')),
    ('NEWLINE',     re.compile(r'\n')),
    ('SKIP',        re.compile(r'[ \t\r]+')),          # whitespace (not newline)
    ('COMMENT',     re.compile(r';[^\n]*')),            # ; to end of line
    ('WORD',        re.compile(r'[A-Za-z_][A-Za-z0-9_]*')),  # identifier / keyword
    ('MISMATCH',    re.compile(r'.')),                  # catch-all for errors
]
 
 
# ── LexerError ────────────────────────────────────────────────────────────────
 
class LexerError(Exception):
    def __init__(self, message, line, col):
        super().__init__(f"[Lexer Error] Line {line}, Col {col}: {message}")
        self.line = line
        self.col  = col
 
 
# ── Lexer class ───────────────────────────────────────────────────────────────
 
class Lexer:
    """
    Hand-written DFA lexer.
    Call tokenize(source) → list of Token objects (NEWLINE tokens included,
    EOF appended at the end).
    """
 
    def __init__(self, source: str):
        self.source = source
 
    def tokenize(self):
        tokens = []
        line   = 1
        col    = 1
        pos    = 0
        src    = self.source
 
        while pos < len(src):
            matched = False
            for tok_type, regex in TOKEN_SPEC:
                m = regex.match(src, pos)
                if m:
                    value = m.group(0)
                    if tok_type == 'SKIP' or tok_type == 'COMMENT':
                        # advance col / pos, no token emitted
                        col += len(value)
                        pos  = m.end()
                        matched = True
                        break
                    elif tok_type == 'NEWLINE':
                        tokens.append(Token('NEWLINE', '\n', line, col))
                        line += 1
                        col   = 1
                        pos   = m.end()
                        matched = True
                        break
                    elif tok_type == 'MISMATCH':
                        raise LexerError(
                            f"Unexpected character: {value!r}", line, col
                        )
                    elif tok_type == 'WORD':
                        # classify as KEYWORD or IDENTIFIER
                        upper = value.upper()
                        if upper in KEYWORDS:
                            tokens.append(Token('KEYWORD', upper, line, col))
                        else:
                            tokens.append(Token('IDENTIFIER', value, line, col))
                        col += len(value)
                        pos  = m.end()
                        matched = True
                        break
                    elif tok_type == 'INT':
                        tokens.append(Token('INT', int(value), line, col))
                        col += len(value)
                        pos  = m.end()
                        matched = True
                        break
                    elif tok_type == 'FLOAT':
                        tokens.append(Token('FLOAT', float(value), line, col))
                        col += len(value)
                        pos  = m.end()
                        matched = True
                        break
                    elif tok_type == 'STRING':
                        # strip surrounding quotes
                        tokens.append(Token('STRING', value[1:-1], line, col))
                        col += len(value)
                        pos  = m.end()
                        matched = True
                        break
                    elif tok_type == 'COLOR_LIT':
                        tokens.append(Token('COLOR_LIT', value.upper(), line, col))
                        col += len(value)
                        pos  = m.end()
                        matched = True
                        break
                    else:
                        tokens.append(Token(tok_type, value, line, col))
                        col += len(value)
                        pos  = m.end()
                        matched = True
                        break
 
            if not matched:
                raise LexerError(f"Cannot tokenize at position {pos}", line, col)
 
        tokens.append(Token('EOF', None, line, col))
        return tokens