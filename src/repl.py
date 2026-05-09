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
        self.buffer     = []
        self.depth      = 0
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

            upper = stripped.upper()
            if any(upper.startswith(kw) for kw in ('LOOP', 'IF')):
                self.depth += 1
            if upper in ('ENDLOOP', 'ENDIF'):
                self.depth -= 1

            self.buffer.append(line)

            if self.depth <= 0:
                source = "\n".join(self.buffer) + "\n"
                self.buffer = []
                self.depth  = 0
                self._execute_snippet(source)

    def _execute_snippet(self, source: str):
        try:
            lexer  = Lexer(source)
            tokens = lexer.tokenize()

            parser = Parser(tokens)
            ast    = parser.parse()

            sa = SemanticAnalyzer()
            sa.palettes = dict(self.analyzer.palettes)
            sa.canvas_declared = self.analyzer.canvas_declared
            for name, info in self.analyzer.sym.scopes[0].items():
                sa.sym.declare(name, info['kind'], info['type'])
            sa.analyze(ast)
            self.analyzer.palettes        = sa.palettes
            self.analyzer.canvas_declared = sa.canvas_declared
            for name, info in sa.sym.scopes[0].items():
                if self.analyzer.sym.lookup(name) is None:
                    self.analyzer.sym.declare(name, info['kind'], info['type'])

            ir_gen = IRGenerator()
            ir_gen._temp_count  = getattr(self, '_temp_counter', 0)
            ir_gen._label_count = getattr(self, '_label_counter', 0)
            instrs = ir_gen.generate(ast)
            self._temp_counter  = ir_gen._temp_count
            self._label_counter = ir_gen._label_count

            opt, _, _ = Optimizer(instrs).optimize()

            saved = dict(self.vm.registers)
            has_canvas = any(i[0] == 'CANVAS' for i in opt)
            if not has_canvas and self.vm.image is not None:
                pass

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
