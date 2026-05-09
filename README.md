# PixLang

A tiny language for drawing pixel art. You write a script, the compiler turns it into a real PNG.

Built for **CS4031 Compiler Construction (Spring 2026)** by:

- Mehroz Muneer — 23K-0748
- Dua Shafiq — 23K-0825
- Kashan Hamid — 23K-0747

## What it is

PixLang is a domain-specific language. You describe a canvas, a palette, and the shapes you want — rectangles, circles, lines, individual pixels — and the compiler renders the result. It also has loops, conditionals, and variables, so you can do procedural patterns instead of hand-placing every shape.

Under the hood it's a textbook six-phase compiler. Source goes in, an image comes out. In between we run lexing, parsing, semantic analysis, IR generation, optimisation, and code generation. Every phase is its own file in `src/` so you can read them top-to-bottom in the order they run.

| Phase | File | What it does |
|------:|------|--------------|
| 1 | `lexer.py` | Hand-written DFA — turns characters into tokens |
| 2 | `parser.py` | Recursive descent — builds an AST |
| 3 | `semantic.py` | Symbol table, type checks, scope rules |
| 4 | `ir_generator.py` | Lowers the AST into Three-Address Code |
| 5 | `optimizer.py` | Constant folding + dead variable elimination |
| 6 | `codegen.py` | Walks the TAC and draws with Pillow |

## Getting it running

You need Python 3.8 or newer and Pillow. That's it.

```
pip install Pillow
```

Then compile any of the test programs:

```
python compiler.py tests/test1_concentric.pix
```

The image lands in `outputs/`. Open it and you should see concentric squares.

## How to use the CLI

The most common things you'll want to do:

```
# Compile a file
python compiler.py tests/test2_flag.pix

# Override the output filename
python compiler.py tests/test2_flag.pix -o my_flag.png

# See every intermediate phase (great for the demo / viva)
python compiler.py tests/test1_concentric.pix --debug

# Type code interactively
python compiler.py --interactive
```

`--debug` is the one we keep going back to — it prints the token stream, the AST, the symbol table, the TAC before and after optimisation, and finally the codegen output. It also tells you how many instructions the optimiser removed.

## Running every test

We ship six sample programs. They cover loops, palette indexing, control flow, error reporting, and a Roblox-style character to make sure the language can do something fun, not just abstract patterns.

```
python compiler.py tests/test1_concentric.pix
python compiler.py tests/test2_flag.pix
python compiler.py tests/test3_checkerboard.pix
python compiler.py tests/test4_starburst.pix
python compiler.py tests/test5_error_demo.pix
python compiler.py tests/test6_character.pix
```

`test5_error_demo.pix` is special — by default it runs as a valid program, but it has five commented-out blocks each demonstrating a different error class. Uncomment one at a time to see the corresponding error message.

## The web playground

If you'd rather not keep editing files and re-running the CLI, there's a small Streamlit app:

```
pip install streamlit
streamlit run ui/app.py
```

It opens at <http://localhost:8501>. Source on the left, "Compile" button, rendered PNG on the right. There's a checkbox to expand the token stream and the optimised TAC if you want to peek at the internals while you edit.

## The language at a glance

A canvas and a palette to start with:

```
CANVAS 64 64
PALETTE retro: #1A1C2C, #5D275D, #B13E53
```

Variables and assignment:

```
VAR size = 60
size = size - 8
```

Drawing:

```
FILL #000000
RECT x, y, width, height, color
CIRCLE cx cy RADIUS r COLOR color
LINE x1 y1 x2 y2 COLOR color
PIXEL x y COLOR color
```

Control flow — the two loop kinds plus IF/ELSE:

```
LOOP WHILE size > 4:
    ...
ENDLOOP

LOOP TIMES 8:
    ...
ENDLOOP

IF rem == 0:
    ...
ELSE:
    ...
ENDIF
```

Saving the result:

```
SAVE "output.png"
```

Comments start with `;`. Palettes are indexed like `retro[0]`. Arithmetic is the usual `+ - * / MOD` with proper precedence and parentheses.

## What the project looks like on disk

```
pixlang/
├── compiler.py        ← entry point you run from the command line
├── README.md
│
├── src/               ← all six compiler phases live here
│   ├── lexer.py
│   ├── parser.py
│   ├── ast_nodes.py
│   ├── semantic.py
│   ├── ir_generator.py
│   ├── optimizer.py
│   ├── codegen.py
│   └── repl.py
│
├── ui/
│   └── app.py         ← Streamlit playground
│
├── tests/             ← sample .pix programs
│   ├── test1_concentric.pix
│   ├── test2_flag.pix
│   ├── test3_checkerboard.pix
│   ├── test4_starburst.pix
│   ├── test5_error_demo.pix
│   └── test6_character.pix
│
├── outputs/           ← images produced by the compiler
│
└── docs/
    ├── proposal.pdf
    └── my_repl_output.png
```

## Errors you might see

We tried to make the messages tell you exactly where things went wrong:

```
[Lexer Error] Line 3, Col 5: Unexpected character '@'

[Parse Error] Line 7, Col 1: Expected 'ENDLOOP' but got EOF

[Semantic Error] Line 4: Drawing command used before CANVAS declaration

[Semantic Error] Line 9: Undefined variable 'x'

[Codegen Error]: Division by zero
```

Each phase has its own exception type, so you always know which stage caught the problem.

## Grammar (EBNF)

```
program       = statement* EOF

statement     = canvas_stmt | palette_stmt | fill_stmt | var_decl
              | assign_stmt | rect_stmt | circle_stmt | line_stmt
              | pixel_stmt  | save_stmt | loop_while | loop_times
              | if_stmt

canvas_stmt   = "CANVAS" expr expr NEWLINE
palette_stmt  = "PALETTE" IDENTIFIER ":" COLOR_LIT ("," COLOR_LIT)* NEWLINE
fill_stmt     = "FILL" color_expr NEWLINE
var_decl      = "VAR" IDENTIFIER "=" expr NEWLINE
assign_stmt   = IDENTIFIER "=" expr NEWLINE

rect_stmt     = "RECT" expr "," expr "," expr "," expr "," color_expr NEWLINE
circle_stmt   = "CIRCLE" expr expr "RADIUS" expr "COLOR" color_expr NEWLINE
line_stmt     = "LINE" expr expr expr expr "COLOR" color_expr NEWLINE
pixel_stmt    = "PIXEL" expr expr "COLOR" color_expr NEWLINE

save_stmt     = "SAVE" STRING NEWLINE

loop_while    = "LOOP" "WHILE" expr ":" NEWLINE statement* "ENDLOOP" NEWLINE
loop_times    = "LOOP" "TIMES" expr ":" NEWLINE statement* "ENDLOOP" NEWLINE

if_stmt       = "IF" expr ":" NEWLINE statement*
                ["ELSE" ":" NEWLINE statement*]
                "ENDIF" NEWLINE

expr          = comparison
comparison    = addition (("<"|">"|"<="|">="|"=="|"!=") addition)?
addition      = term (("+"|"-") term)*
term          = factor (("*"|"/"|"MOD") factor)*

factor        = "-" factor | "(" expr ")" | atom

atom          = INT | FLOAT | COLOR_LIT | STRING | palette_index | IDENTIFIER

color_expr    = COLOR_LIT | palette_index | IDENTIFIER

palette_index = IDENTIFIER "[" expr "]"
```

## Tokens the lexer recognises

**Keywords:**
`CANVAS`, `PALETTE`, `FILL`, `VAR`, `LOOP`, `WHILE`, `TIMES`, `ENDLOOP`, `IF`, `ELSE`, `ENDIF`, `RECT`, `CIRCLE`, `LINE`, `PIXEL`, `SAVE`, `RADIUS`, `COLOR`, `MOD`

**Literals:**

| Kind | Pattern |
|------|---------|
| `IDENTIFIER` | `[A-Za-z_][A-Za-z0-9_]*` |
| `INT` | `[0-9]+` |
| `FLOAT` | `[0-9]+\.[0-9]+` |
| `COLOR_LIT` | `#[0-9A-Fa-f]{3,6}` |
| `STRING` | `"[^"]*"` |
| `COMMENT` | `;[^\n]*` (skipped) |

**Operators:** `+ - * / ( ) [ ] , : = < > <= >= == !=`

## What the optimiser actually does

There are two passes worth showing off, both visible with `--debug`.

**Constant folding** — the optimiser evaluates expressions whose operands are all known at compile time:

```
Before:        After:
t1 = 32 - 8    t1 = 24
```

**Dead variable elimination** — if a temporary is assigned but never read, it's removed:

```
Before:           After:
t3 = col + 1      col = t3
col = t3
t4 = 5            (t4 is gone — nothing reads it)
```

Run any program with `--debug` and you'll see the exact instruction counts before and after the pass, plus how many instructions were removed.
