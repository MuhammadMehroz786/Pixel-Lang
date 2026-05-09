#!/usr/bin/env python3
# =============================================================================
# compiler.py — PixLang Compiler Entry Point
#
# Usage:
#   python compiler.py input.pix                  compile and run
#   python compiler.py input.pix -o output.png    specify output filename
#   python compiler.py input.pix --debug          show all IR phases
#   python compiler.py --interactive              start REPL
#
# Exit codes:
#   0  success
#   1  compile or runtime error
# =============================================================================
 
import sys
import os
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from lexer        import Lexer,    LexerError
from parser       import Parser,   ParseError
from semantic     import SemanticAnalyzer, SemanticError
from ir_generator import IRGenerator
from optimizer    import Optimizer
from codegen      import VirtualMachine, CodegenError
 
 
# ── Helpers ───────────────────────────────────────────────────────────────────
 
def print_section(title: str, content: str):
    bar = "=" * 60
    print(f"\n{bar}")
    print(f"  {title}")
    print(bar)
    print(content)
 
 
def compile_source(source: str, source_name: str, debug: bool = False):
    """
    Run all compiler phases on source text.
    Returns the optimized instruction list.
    Raises SystemExit on any error.
    """
 
    # ── Phase 1: Lexical Analysis ─────────────────────────────────────────────
    try:
        lexer  = Lexer(source)
        tokens = lexer.tokenize()
    except LexerError as e:
        print(e)
        sys.exit(1)
 
    if debug:
        token_lines = "\n".join(
            f"  {t.type:12s}  {str(t.value):30s}  L{t.line}:C{t.col}"
            for t in tokens if t.type != 'EOF'
        )
        print_section("Phase 1 — Token Stream", token_lines)
 
    # ── Phase 2: Syntax Analysis (Parsing) ────────────────────────────────────
    try:
        parser = Parser(tokens)
        ast    = parser.parse()
    except ParseError as e:
        print(e)
        sys.exit(1)
 
    if debug:
        print_section("Phase 2 — Abstract Syntax Tree", repr(ast))
 
    # ── Phase 3: Semantic Analysis ────────────────────────────────────────────
    try:
        analyzer = SemanticAnalyzer()
        sym_table = analyzer.analyze(ast)
    except SemanticError as e:
        print(e)
        sys.exit(1)
 
    if debug:
        print_section("Phase 3 — Symbol Table", sym_table.dump())
 
    # ── Phase 4: IR Generation ────────────────────────────────────────────────
    ir_gen = IRGenerator()
    raw_ir = ir_gen.generate(ast)
 
    if debug:
        print_section("Phase 4 — Three-Address Code (before optimisation)",
                      ir_gen.pretty_print())
 
    # ── Phase 5: Optimisation ─────────────────────────────────────────────────
    opt_engine = Optimizer(raw_ir)
    optimized, before_count, after_count = opt_engine.optimize()
 
    if debug:
        print_section(
            f"Phase 5 — Optimised TAC  "
            f"({before_count} → {after_count} instructions, "
            f"{before_count - after_count} removed)",
            Optimizer.pretty_print(optimized)
        )
 
    return optimized
 
 
def run_codegen(instructions, debug: bool = False):
    """Execute the instruction list via the virtual machine."""
    vm = VirtualMachine()
    try:
        saved = vm.execute(instructions)
        if saved:
            for f in saved:
                print(f"  Output: {os.path.abspath(f)}")
        else:
            print("  (No SAVE statement found — no image written)")
    except CodegenError as e:
        print(e)
        sys.exit(1)
 
 
# ── CLI argument parsing ──────────────────────────────────────────────────────
 
def build_parser():
    p = argparse.ArgumentParser(
        prog='compiler',
        description='PixLang Compiler — compile .pix files to PNG images'
    )
    p.add_argument('input', nargs='?',
                   help='Source file (.pix)')
    p.add_argument('-o', '--output',
                   help='Output PNG filename (overrides SAVE in source)')
    p.add_argument('--debug', action='store_true',
                   help='Print all intermediate representations')
    p.add_argument('--interactive', action='store_true',
                   help='Start interactive REPL mode')
    return p
 
 
# ── Main ──────────────────────────────────────────────────────────────────────
 
def main():
    arg_parser = build_parser()
    args       = arg_parser.parse_args()
 
    # ── Interactive REPL mode ─────────────────────────────────────────────────
    if args.interactive:
        from repl import REPL
        REPL().run()
        return
 
    # ── File compilation mode ─────────────────────────────────────────────────
    if not args.input:
        arg_parser.print_help()
        sys.exit(0)
 
    if not os.path.isfile(args.input):
        print(f"[Error] File not found: {args.input}")
        sys.exit(1)
 
    with open(args.input, 'r', encoding='utf-8') as f:
        source = f.read()
 
    print(f"\n  PixLang Compiler — compiling '{args.input}'")
    print("  " + "-" * 40)
 
    instructions = compile_source(source, args.input, debug=args.debug)
 
    # If user specified -o, patch SAVE instructions
    if args.output:
        instructions = [
            ('SAVE', args.output, None, None) if i[0] == 'SAVE' else i
            for i in instructions
        ]
 
    # ── Phase 6: Code Generation ──────────────────────────────────────────────
    if args.debug:
        print("\n" + "=" * 60)
        print("  Phase 6 — Code Generation (Pillow VM)")
        print("=" * 60)
 
    run_codegen(instructions, debug=args.debug)
    print("\n  Compilation successful.\n")
 
 
if __name__ == '__main__':
    main()