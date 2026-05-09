

# =============================================================================
# repl.py — PixLang Interactive REPL (Read-Eval-Print Loop)
#
# Usage:  python compiler.py --interactive
#
# The REPL maintains a persistent virtual machine across commands so that
# a CANVAS declared in one line is still active in the next.
# Type 'exit' or 'quit' to leave.  Type 'save <filename>' to write PNG.
# Type 'reset' to start a fresh canvas.
# Type 'help' to list available commands.
# =============================================================================
 
from lexer        import Lexer,    LexerError
from parser       import Parser,   ParseError
from semantic     import SemanticAnalyzer, SemanticError
from ir_generator import IRGenerator
from optimizer    import Optimizer
from codegen      import VirtualMachine, CodegenError
 
BANNER = r"""
  ____  _      _                       ____  _____ ____  _
 |  _ \(_)_  _| |    __ _ _ __   __ _|  _ \| ____|  _ \| |
 | |_) | \ \/ / |   / _` | '_ \ / _` | |_) |  _| | |_) | |
 |  __/| |>  <| |__| (_| | | | | (_| |  _ <| |___|  __/| |___
 |_|   |_/_/\_\_____\__,_|_| |_|\__, |_| \_\_____|_|   |_____|
                                 |___/
  PixLang Interactive REPL  —  type 'help' for commands
"""
 
HELP_TEXT = """
Commands:
  CANVAS <w> <h>            — create a canvas (required first)
  PALETTE <name>: #hex,...  — define a colour palette
  FILL <color>              — fill the entire canvas
  VAR <name> = <expr>       — declare a variable
  <name> = <expr>           — reassign a variable
  RECT x,y,w,h,color        — draw a rectangle
  CIRCLE cx cy RADIUS r COLOR c — draw a circle
  LINE x1 y1 x2 y2 COLOR c  — draw a line
  PIXEL x y COLOR c         — draw a single pixel
  SAVE "<filename.png>"     — write the canvas to disk
  LOOP WHILE / LOOP TIMES   — loops (multi-line; end with ENDLOOP)
  IF ... ELSE ... ENDIF     — conditionals (multi-line)
 
  reset   — clear canvas and variables
  help    — show this help
  exit    — quit the REPL
"""
 
 
class REPL:
    def __init__(self):
        self._reset()
 
    def _reset(self):
        self.vm         = VirtualMachine()
        self.analyzer   = SemanticAnalyzer()
        self.buffer     = []   # accumulates lines for multi-line blocks
        self.depth      = 0    # nesting depth (LOOP/IF increments, ENDLOOP/ENDIF decrements)
        print("[REPL] Canvas reset.")
 
    def run(self):
        print(BANNER)
        while True:
            try:
                prompt = "... " if self.depth > 0 else ">>> "
                line   = input(prompt)
            except (EOFError, KeyboardInterrupt):
                print("\nBye!")
                break
 
            stripped = line.strip()
 
            # ── Meta commands ─────────────────────────────────────────────────
            if self.depth == 0:
                if stripped.lower() in ('exit', 'quit'):
                    print("Bye!")
                    break
                if stripped.lower() == 'reset':
                    self._reset()
                    continue
                if stripped.lower() == 'help':
                    print(HELP_TEXT)
                    continue
                if stripped == '':
                    continue
 
            # ── Buffer accumulation for multi-line blocks ─────────────────────
            upper = stripped.upper()
            if any(upper.startswith(kw) for kw in ('LOOP', 'IF')):
                self.depth += 1
            if upper in ('ENDLOOP', 'ENDIF'):
                self.depth -= 1
 
            self.buffer.append(line)
 
            # ── Execute when we have a complete block ─────────────────────────
            if self.depth <= 0:
                source = "\n".join(self.buffer) + "\n"
                self.buffer = []
                self.depth  = 0
                self._execute_snippet(source)
 
    def _execute_snippet(self, source: str):
        try:
            # Lex
            lexer  = Lexer(source)
            tokens = lexer.tokenize()
 
            # Parse
            parser = Parser(tokens)
            ast    = parser.parse()
 
            # Semantic check — use a fresh analyser but share palette/canvas state
            sa = SemanticAnalyzer()
            # Carry over known palettes so palette references work across lines
            sa.palettes = dict(self.analyzer.palettes)
            sa.canvas_declared = self.analyzer.canvas_declared
            # Merge existing symbols into global scope
            for name, info in self.analyzer.sym.scopes[0].items():
                sa.sym.declare(name, info['kind'], info['type'])
            sa.analyze(ast)
            # Persist updated state
            self.analyzer.palettes        = sa.palettes
            self.analyzer.canvas_declared = sa.canvas_declared
            for name, info in sa.sym.scopes[0].items():
                if self.analyzer.sym.lookup(name) is None:
                    self.analyzer.sym.declare(name, info['kind'], info['type'])
 
            # IR generation
            ir_gen = IRGenerator()
            # Carry over temp counter so temps don't collide across snippets
            ir_gen._temp_count  = getattr(self, '_temp_counter', 0)
            ir_gen._label_count = getattr(self, '_label_counter', 0)
            instrs = ir_gen.generate(ast)
            self._temp_counter  = ir_gen._temp_count
            self._label_counter = ir_gen._label_count
 
            # Optimize
            opt, _, _ = Optimizer(instrs).optimize()
 
            # Execute on persistent VM
            # Transfer register state (user variables)
            saved = dict(self.vm.registers)
            # Re-init VM image only if CANVAS appears in this snippet
            has_canvas = any(i[0] == 'CANVAS' for i in opt)
            if not has_canvas and self.vm.image is not None:
                # Restore previous image state variables
                pass   # VM keeps its image
 
            self.vm.execute(opt)
 
        except LexerError as e:
            print(f"  {e}")
        except ParseError as e:
            print(f"  {e}")
        except SemanticError as e:
            print(f"  {e}")
        except CodegenError as e:
            print(f"  {e}")
        except Exception as e:
            print(f"  [Error] {e}")