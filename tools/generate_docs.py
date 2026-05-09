"""Generate the three short submission docs for PixLang.

Mirrors the structure and length of the RetroLogo project's docs:
single heading + a short paragraph, ~one page each.
"""
import os
from docx import Document
from docx.shared import Pt, RGBColor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs")
os.makedirs(OUT, exist_ok=True)


def make_doc(filename, heading, body):
    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)
    style.font.color.rgb = RGBColor(0, 0, 0)

    h = doc.add_heading(heading, level=1)
    for run in h.runs:
        run.font.color.rgb = RGBColor(0, 0, 0)

    for para in body.strip().split("\n\n"):
        p = doc.add_paragraph()
        run = p.add_run(para.strip())
        run.font.color.rgb = RGBColor(0, 0, 0)

    path = os.path.join(OUT, filename)
    doc.save(path)
    print(f"  wrote {path}")


# ── Document 1: Team Reflection ─────────────────────────────────────────────

team_reflection = """
Working on PixLang gave us a much clearer picture of what actually happens
between writing a piece of source code and seeing a result on screen. Splitting
the compiler into six discrete phases, lexer, parser, semantic analyser, IR
generator, optimiser, and code generator, forced us to think about each stage
in isolation rather than as one big translation step.

Team contributions:

Mehroz Muneer (23K-0748) led the front-end of the compiler. He built the
hand-written DFA lexer and the recursive-descent parser, designed the AST
node hierarchy in ast_nodes.py, and produced the EBNF grammar that the
parser implements. He also set up the CLI driver in compiler.py, integrated
the six phases into a single pipeline, and authored the --debug output that
prints every intermediate representation. Most of the test programs in
tests/ were written and debugged by him as the language took shape.

Dua Shafiq (23K-0825) was responsible for the middle and back-end. She wrote
the semantic analyser including the scoped symbol table and the type system
(INT, FLOAT, COLOR, STRING), handled CANVAS-before-drawing validation and
palette resolution, and produced the line-accurate semantic error messages.
She also implemented the IR generator that lowers the AST to Three-Address
Code and the optimiser passes, constant folding and dead-variable
elimination, that make the --debug instruction counts drop visibly.

Kashan Hamid (23K-0747) owned code generation, tooling, and the user-facing
parts of the project. He built the TAC interpreter / virtual machine in
codegen.py that drives the Pillow image library, the interactive REPL, and
the Streamlit playground in ui/app.py. He generated the parse-tree, DFA,
and symbol-table diagrams under diagrams/, organised the project into its
final src / ui / tests / outputs / docs layout, and wrote and maintained
the README.

The hardest parts were the parser and the semantic analyser. Recursive descent
looks straightforward in theory, but handling operator precedence, palette
indexing, and statements that span multiple lines (like LOOP and IF blocks)
required a lot of careful planning. Semantic analysis was tricky in a different
way, keeping the symbol table consistent across nested scopes and producing
useful error messages took several rewrites before it felt right.

Generating Three-Address Code and watching the optimiser fold constants and
remove dead variables was the most satisfying part. It made the theory from
class concrete: we could literally see the instruction count drop in the
--debug output. If we extended PixLang we would add user-defined functions,
nested palettes, and a richer optimiser (common subexpression elimination,
loop-invariant code motion). We would also like to expand the Streamlit
playground into a proper IDE with syntax highlighting and live preview.
"""

# ── Document 2: Compiler Architecture ───────────────────────────────────────

compiler_architecture = """
PixLang compiles a .pix source file into a PNG image through a six-phase
pipeline:

Source Code → Lexer → Parser → Semantic Analyser → IR Generator → Optimiser → Code Generator → PNG

The Lexer is a hand-written deterministic finite automaton that converts the
input character stream into a list of tokens (keywords, identifiers, integer
and float literals, color literals, strings, operators, and punctuation).
Comments beginning with ';' and whitespace are discarded.

The Parser is a recursive-descent parser that consumes the token stream and
builds an Abstract Syntax Tree using the node classes defined in ast_nodes.py.
It enforces the grammar of statements, expressions, and control-flow blocks.

The Semantic Analyser walks the AST, builds a scoped symbol table, infers
expression types (INT, FLOAT, COLOR, STRING), validates that drawing commands
appear after a CANVAS declaration, and checks palette references.

The IR Generator lowers the validated AST into Three-Address Code, a flat
linear sequence of simple instructions that resemble assembly. The Optimiser
then performs constant folding (evaluating constant sub-expressions at
compile time) and dead variable elimination (removing temporaries that are
written but never read).

Finally, the Code Generator interprets the optimised TAC instructions on a
small virtual machine that drives the Pillow image library to draw rectangles,
circles, lines, and individual pixels onto the canvas, and writes the result
to a PNG file.
"""

# ── Document 3: Language Reference Manual ───────────────────────────────────

language_reference = """
PixLang is a small domain-specific language for procedurally generating pixel
art. A program describes a canvas, an optional set of named palettes, and a
sequence of drawing commands. Loops, conditionals, variables, and arithmetic
expressions allow patterns to be described compactly rather than pixel by
pixel.

Keywords: CANVAS, PALETTE, FILL, VAR, LOOP, WHILE, TIMES, ENDLOOP, IF, ELSE,
ENDIF, RECT, CIRCLE, LINE, PIXEL, SAVE, RADIUS, COLOR, MOD.

Tokens: identifiers match [A-Za-z_][A-Za-z0-9_]*. Integers and floats are
standard. Color literals are hexadecimal (#RGB or #RRGGBB). Strings are
double-quoted. Comments begin with ';' and run to end of line.

Drawing commands operate on the current canvas:
  RECT x, y, width, height, color
  CIRCLE cx cy RADIUS r COLOR color
  LINE x1 y1 x2 y2 COLOR color
  PIXEL x y COLOR color
  FILL color

Variables are declared with VAR and reassigned without VAR. Arithmetic
supports +, -, *, /, MOD with full operator precedence and parentheses.
Comparisons (<, >, <=, >=, ==, !=) yield numeric truth values used in
conditions.

Example grammar (simplified):
  program     ::= statement*
  statement   ::= canvas_stmt | palette_stmt | draw_stmt | var_decl
                | assign | loop_stmt | if_stmt | save_stmt
  loop_stmt   ::= "LOOP" ("WHILE" expr | "TIMES" expr) ":" statement* "ENDLOOP"

Palettes are declared with PALETTE name: #hex, #hex, ... and indexed as
name[i]. Programs end with SAVE "file.png" to write the rendered canvas.
The compiler performs constant folding and dead-variable elimination on
the intermediate representation before code generation.
"""

# ── Document 4: Test Suite ──────────────────────────────────────────────────

test_suite = """
PixLang ships with six test programs in tests/, each chosen to exercise a
different combination of language features. Running a test produces a PNG in
outputs/, which can be compared against the reference image bundled in the
same folder. All six programs are expected to compile and produce identical
pixel output across runs.

Test 1: test1_concentric.pix (64 x 64).
Exercises palettes, palette indexing, VAR declarations, arithmetic with
parentheses and division, the MOD operator, and a LOOP WHILE block. Draws
concentric rectangles around a central circle. Expected output: nested
coloured squares on a dark background.

Test 2: test2_flag.pix (90 x 60).
The simplest program in the suite. No variables, no loops, just FILL plus
three RECT commands and a SAVE. Used as a sanity check that the parser and
codegen handle linear straight-line programs correctly. Expected output:
three horizontal stripes (red, white, green).

Test 3: test3_checkerboard.pix (64 x 64).
Exercises nested LOOP TIMES blocks together with an IF / ELSE inside the
inner loop. Demonstrates that scope handling in the semantic analyser is
correct across multiple nested blocks. Expected output: a regular
checkerboard pattern.

Test 4: test4_starburst.pix (128 x 128).
Exercises the LINE primitive together with palette indexing. Eight LINE
statements draw rays from the centre of the canvas to each of the eight
compass directions, each tinted with a different colour from an 8-entry
palette, with a small CIRCLE finishing the centre. Expected output: a
multicoloured starburst on a black background.

Test 5: test5_error_demo.pix.
A two-mode test. By default it compiles successfully (a fallback program
that draws three coloured rectangles) so that the run-all script does not
fail. The file also contains five commented-out blocks, each demonstrating
a different error class:
  • Lexer error: invalid character ('@')
  • Parser error: missing ENDLOOP
  • Semantic error: drawing command before CANVAS
  • Semantic error: undeclared variable
  • Semantic error: wrong SAVE extension (.bmp)
Uncomment one block at a time to see the corresponding diagnostic.

Test 6: test6_character.pix (256 x 320).
A blocky, Roblox-style figure built entirely from RECT and PIXEL commands.
Demonstrates that the language is expressive enough for hand-authored
sprite art at a larger canvas size, and acts as a visually striking demo
during the viva. Expected output: a yellow-headed, blue-shirted, red-trousered
character on a dark background.

Running the full suite:
  python compiler.py tests/test1_concentric.pix
  python compiler.py tests/test2_flag.pix
  python compiler.py tests/test3_checkerboard.pix
  python compiler.py tests/test4_starburst.pix
  python compiler.py tests/test5_error_demo.pix
  python compiler.py tests/test6_character.pix

Each command writes its image into outputs/ and prints "Compilation
successful." on success. Add --debug to any command to see the token stream,
AST, symbol table, raw and optimised TAC, and the codegen log for that
program.
"""

if __name__ == "__main__":
    make_doc("Team_Reflection.docx",          "Team Reflection",          team_reflection)
    make_doc("CompilerArchitecture.docx",     "Compiler Architecture",    compiler_architecture)
    make_doc("LanguageReferenceManual.docx",  "Language Reference Manual", language_reference)
    make_doc("TestSuite.docx",                "Test Suite",                test_suite)
