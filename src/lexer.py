import re


class Token:
    __slots__ = ('type', 'value', 'line', 'col')

    def __init__(self, type_, value, line, col):
        self.type  = type_
        self.value = value
        self.line  = line
        self.col   = col

    def __repr__(self):
        return f"Token({self.type}, {self.value!r}, L{self.line}:C{self.col})"


KEYWORDS = {
    'CANVAS', 'PALETTE', 'FILL', 'VAR', 'LOOP', 'WHILE', 'TIMES',
    'ENDLOOP', 'IF', 'ELSE', 'ENDIF', 'RECT', 'CIRCLE', 'LINE',
    'PIXEL', 'SAVE', 'RADIUS', 'COLOR', 'MOD',
}

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
    ('SKIP',        re.compile(r'[ \t\r]+')),
    ('COMMENT',     re.compile(r';[^\n]*')),
    ('WORD',        re.compile(r'[A-Za-z_][A-Za-z0-9_]*')),
    ('MISMATCH',    re.compile(r'.')),
]


class LexerError(Exception):
    def __init__(self, message, line, col):
        super().__init__(f"[Lexer Error] Line {line}, Col {col}: {message}")
        self.line = line
        self.col  = col


class Lexer:
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
