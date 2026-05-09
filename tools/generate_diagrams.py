"""Generate parse tree, DFA, and symbol table diagrams for two test programs.

Produces 6 PNGs in diagrams/:
  - test1_concentric_parse_tree.png
  - test1_concentric_dfa.png
  - test1_concentric_symbol_table.png
  - test2_flag_parse_tree.png
  - test2_flag_dfa.png
  - test2_flag_symbol_table.png
"""
import os
import sys
import math

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from lexer import Lexer
from parser import Parser
from semantic import SemanticAnalyzer
import ast_nodes as A


# ─── Parse Tree ──────────────────────────────────────────────────────────────

def node_label(n):
    """Single-line label for an AST node (avoids matplotlib bbox clipping)."""
    if isinstance(n, A.Program):       return "Program"
    if isinstance(n, A.CanvasStmt):    return "CANVAS"
    if isinstance(n, A.PaletteStmt):   return f"PALETTE {n.name}"
    if isinstance(n, A.FillStmt):      return "FILL"
    if isinstance(n, A.VarDecl):       return f"VAR {n.name}"
    if isinstance(n, A.AssignStmt):    return f"ASSIGN {n.name}"
    if isinstance(n, A.RectStmt):      return "RECT"
    if isinstance(n, A.CircleStmt):    return "CIRCLE"
    if isinstance(n, A.LineStmt):      return "LINE"
    if isinstance(n, A.PixelStmt):     return "PIXEL"
    if isinstance(n, A.SaveStmt):      return f"SAVE \"{n.filename}\""
    if isinstance(n, A.LoopWhile):     return "LOOP WHILE"
    if isinstance(n, A.LoopTimes):     return "LOOP TIMES"
    if isinstance(n, A.IfStmt):        return "IF"
    if isinstance(n, A.BinOp):         return n.op
    if isinstance(n, A.UnaryOp):       return f"u{n.op}"
    if isinstance(n, A.NumberLit):     return str(n.value)
    if isinstance(n, A.StringLit):     return f'"{n.value}"'
    if isinstance(n, A.ColorLit):      return n.value
    if isinstance(n, A.Identifier):    return n.name
    if isinstance(n, A.PaletteIndex):  return f"{n.palette_name}[ ]"
    return type(n).__name__

def node_children(n):
    """Ordered list of (label, child_node) for tree edges."""
    if isinstance(n, A.Program):       return [("", s) for s in n.statements]
    if isinstance(n, A.CanvasStmt):    return [("w", n.width), ("h", n.height)]
    if isinstance(n, A.FillStmt):      return [("color", n.color)]
    if isinstance(n, A.VarDecl):       return [("=", n.expr)]
    if isinstance(n, A.AssignStmt):    return [("=", n.expr)]
    if isinstance(n, A.RectStmt):
        return [("x", n.x), ("y", n.y), ("w", n.w), ("h", n.h), ("c", n.color)]
    if isinstance(n, A.CircleStmt):
        return [("cx", n.cx), ("cy", n.cy), ("r", n.radius), ("c", n.color)]
    if isinstance(n, A.LoopWhile):
        return [("cond", n.condition)] + [("", s) for s in n.body]
    if isinstance(n, A.LoopTimes):
        return [("n", n.times)] + [("", s) for s in n.body]
    if isinstance(n, A.IfStmt):
        out = [("cond", n.condition)] + [("then", s) for s in n.then_body]
        if n.else_body:
            out += [("else", s) for s in n.else_body]
        return out
    if isinstance(n, A.BinOp):         return [("L", n.left), ("R", n.right)]
    if isinstance(n, A.UnaryOp):       return [("", n.operand)]
    if isinstance(n, A.PaletteIndex):  return [("idx", n.index_expr)]
    return []


def layout_tree(root):
    """Walker-style layout: assigns (x, y) to every node. Returns nodes, edges."""
    positions = {}
    edges = []
    leaf_x = [0]
    LEAF_GAP = 3.5

    def walk(node, depth, parent_id, parent_x, parent_label):
        nid = len(positions)
        children = node_children(node)
        if not children:
            x = leaf_x[0]
            leaf_x[0] += LEAF_GAP
        else:
            child_xs = []
            for lbl, ch in children:
                cid = walk(ch, depth + 1, nid, None, lbl)
                child_xs.append(positions[cid][0])
            x = (min(child_xs) + max(child_xs)) / 2
        positions[nid] = (x, -depth * 1.8, node_label(node))
        if parent_id is not None:
            edges.append((parent_id, nid, parent_label))
        return nid

    walk(root, 0, None, None, "")
    return positions, edges


def draw_parse_tree(ast, title, out_path):
    positions, edges = layout_tree(ast)
    if not positions:
        return
    xs  = [p[0] for p in positions.values()]
    ys  = [p[1] for p in positions.values()]
    span_x = max(xs) - min(xs)
    span_y = max(ys) - min(ys)

    # cap figure size so output PNG is sensibly sized
    width  = min(22, max(11, span_x * 0.32 + 3))
    height = min(14, max(6, span_y * 0.55 + 2))

    fig, ax = plt.subplots(figsize=(width, height))
    ax.set_axis_off()
    ax.set_title(title, fontsize=15, weight="bold", pad=12)

    for a, b, lbl in edges:
        ax1, ay1, _ = positions[a]
        bx, by, _ = positions[b]
        ax.plot([ax1, bx], [ay1, by], color="#888", lw=1.0, zorder=1)
        if lbl:
            # Place edge label 30% down from parent — keeps it off the child node
            mx = ax1 + (bx - ax1) * 0.30
            my = ay1 + (by - ay1) * 0.30
            ax.text(mx, my, lbl, fontsize=7, color="#555",
                    style="italic", zorder=1.5)

    for nid, (x, y, lbl) in positions.items():
        is_leaf = not any(e[0] == nid for e in edges)
        fc = "#FFE0B5" if is_leaf else "#B5D8FF"
        ec = "#C9853B" if is_leaf else "#3367C9"
        ax.text(x, y, lbl, ha="center", va="center", fontsize=9,
                bbox=dict(boxstyle="round,pad=0.4", fc=fc, ec=ec, lw=1.2),
                zorder=4)

    pad_x = max(1.0, span_x * 0.03)
    pad_y = max(0.5, span_y * 0.06)
    ax.set_xlim(min(xs) - pad_x, max(xs) + pad_x)
    ax.set_ylim(min(ys) - pad_y, max(ys) + pad_y + 0.3)
    plt.savefig(out_path, dpi=110, bbox_inches="tight", pad_inches=0.3)
    plt.close(fig)


# ─── DFA ─────────────────────────────────────────────────────────────────────

def draw_dfa(out_path, title="PixLang Lexer DFA"):
    """Draws the master DFA the lexer effectively implements."""
    fig, ax = plt.subplots(figsize=(18, 11))
    ax.set_axis_off()
    ax.set_title(title, fontsize=15, weight="bold", pad=14)

    states = {
        "S0":   (0, 0, "Start"),
        "ID":   (3.5, 2.5, "IDENTIFIER\n/ KEYWORD"),
        "INT":  (3.5, 0.8, "INT"),
        "FLT":  (6.5, 0.8, "FLOAT"),
        "HASH": (3.5, -1.0, "#"),
        "COL":  (6.5, -1.0, "COLOR_LIT"),
        "STR1": (3.5, -2.7, '"...'),
        "STR":  (6.5, -2.7, "STRING"),
        "CMT1": (3.5, -4.3, "; ..."),
        "CMT":  (6.5, -4.3, "(skip)"),
        "OP":   (-3.5, 1.5, "OP"),
        "OP2":  (-6.5, 1.5, "OP\n(<=,>=,==,!=)"),
        "PUN":  (-3.5, -1.5, "PUNCT\n( ) [ ] , :"),
        "ERR":  (0, -5.7, "Lexer\nError"),
    }
    accepting = {"ID", "INT", "FLT", "COL", "STR", "CMT", "OP", "OP2", "PUN"}

    transitions = [
        ("S0",  "ID",   "letter | _"),
        ("ID",  "ID",   "letter | digit | _"),
        ("S0",  "INT",  "digit"),
        ("INT", "INT",  "digit"),
        ("INT", "FLT",  "."),
        ("FLT", "FLT",  "digit"),
        ("S0",  "HASH", "#"),
        ("HASH","COL",  "[0-9a-fA-F] (3-6 times)"),
        ("S0",  "STR1", '"'),
        ("STR1","STR1", "any except \""),
        ("STR1","STR",  '"'),
        ("S0",  "CMT1", ";"),
        ("CMT1","CMT1", "any except newline"),
        ("CMT1","CMT",  "newline"),
        ("S0",  "OP",   "+ - * / < > ="),
        ("OP",  "OP2",  "= (after < > = !)"),
        ("S0",  "PUN",  "( ) [ ] , :"),
        ("S0",  "ERR",  "@ $ % ... unknown"),
    ]

    # state circles
    for sid, (x, y, lbl) in states.items():
        r = 0.55
        fc = "#B5E8B5" if sid in accepting else "#E8E8E8"
        ec = "#2E7D32" if sid in accepting else "#666"
        if sid == "ERR":
            fc, ec = "#FFC4C4", "#B22222"
        ax.add_patch(Circle((x, y), r, fc=fc, ec=ec, lw=1.6, zorder=2))
        if sid in accepting:
            ax.add_patch(Circle((x, y), r * 0.78, fc="none",
                                ec=ec, lw=1.0, zorder=3))
        ax.text(x, y, lbl, ha="center", va="center", fontsize=9, zorder=4)

    def edge(a, b, lbl, curve=0.0):
        ax_, ay_, _ = states[a]
        bx, by, _ = states[b]
        rad = 0.55
        # shrink endpoints
        dx, dy = bx - ax_, by - ay_
        d = math.hypot(dx, dy) or 1
        ax_s = ax_ + dx / d * rad
        ay_s = ay_ + dy / d * rad
        bx_s = bx - dx / d * rad
        by_s = by - dy / d * rad
        if a == b:
            arrow = FancyArrowPatch((ax_ - 0.4, ay_ + 0.6), (ax_ + 0.4, ay_ + 0.6),
                                    connectionstyle="arc3,rad=1.2",
                                    arrowstyle="->", mutation_scale=12,
                                    color="#444")
            ax.add_patch(arrow)
            ax.text(ax_, ay_ + 1.25, lbl, fontsize=8, ha="center", color="#222")
        else:
            arrow = FancyArrowPatch((ax_s, ay_s), (bx_s, by_s),
                                    connectionstyle=f"arc3,rad={curve}",
                                    arrowstyle="->", mutation_scale=12,
                                    color="#444", lw=1.0)
            ax.add_patch(arrow)
            mx, my = (ax_ + bx) / 2, (ay_ + by) / 2
            ax.text(mx + curve * 0.4, my + curve * 0.4, lbl, fontsize=8,
                    ha="center", color="#222",
                    bbox=dict(boxstyle="round,pad=0.15", fc="white",
                              ec="none", alpha=0.85))

    curves = {("ID","ID"):0, ("INT","INT"):0, ("FLT","FLT"):0,
              ("STR1","STR1"):0, ("CMT1","CMT1"):0}
    for a, b, lbl in transitions:
        edge(a, b, lbl, curve=0.15 if a != b else 0)

    # start arrow
    sx, sy, _ = states["S0"]
    ax.add_patch(FancyArrowPatch((sx - 1.6, sy), (sx - 0.55, sy),
                                 arrowstyle="->", mutation_scale=14,
                                 color="black", lw=1.4))
    ax.text(sx - 1.7, sy + 0.18, "start", fontsize=8)

    # legend
    leg = [
        mpatches.Patch(facecolor="#E8E8E8", edgecolor="#666", label="Non-accepting"),
        mpatches.Patch(facecolor="#B5E8B5", edgecolor="#2E7D32", label="Accepting (token emitted)"),
        mpatches.Patch(facecolor="#FFC4C4", edgecolor="#B22222", label="Error state"),
    ]
    ax.legend(handles=leg, loc="lower right", fontsize=8, framealpha=0.95)

    ax.set_xlim(-9, 9)
    ax.set_ylim(-7, 4)
    ax.set_aspect("equal")
    plt.savefig(out_path, dpi=130)
    plt.close(fig)


# ─── Symbol Table ────────────────────────────────────────────────────────────

def collect_symbols(program):
    """Walk AST + run analyser to gather every (scope, name, kind, type, line)."""
    rows = []

    class TracingTable:
        def __init__(self):
            self.scopes = [("global", {})]
            self.depth_counter = 0
        def push_scope(self, label="block"):
            self.depth_counter += 1
            self.scopes.append((f"{label}#{self.depth_counter}", {}))
        def pop_scope(self):
            if len(self.scopes) > 1:
                self.scopes.pop()
        def declare(self, name, kind, type_, line=None):
            scope_name, scope_dict = self.scopes[-1]
            scope_dict[name] = {"kind": kind, "type": type_, "line": line}
            rows.append((scope_name, name, kind, type_, line))
        def lookup(self, name):
            for _, sd in reversed(self.scopes):
                if name in sd:
                    return sd[name]
            return None

    analyzer = SemanticAnalyzer()
    analyzer.sym = TracingTable()

    def push_with_label(label):
        analyzer.sym.push_scope(label)

    # walk and record — replicate semantic.check_stmt with scope labels
    def visit(node):
        if isinstance(node, A.PaletteStmt):
            analyzer.sym.declare(node.name, "PALETTE", "PALETTE", node.line)
        elif isinstance(node, A.VarDecl):
            t = analyzer.check_expr(node.expr)
            analyzer.sym.declare(node.name, "VAR", t, node.line)
        elif isinstance(node, A.CanvasStmt):
            analyzer.canvas_declared = True
        elif isinstance(node, A.LoopWhile):
            push_with_label("while")
            for s in node.body: visit(s)
            analyzer.sym.pop_scope()
        elif isinstance(node, A.LoopTimes):
            push_with_label("times")
            for s in node.body: visit(s)
            analyzer.sym.pop_scope()
        elif isinstance(node, A.IfStmt):
            push_with_label("if-then")
            for s in node.then_body: visit(s)
            analyzer.sym.pop_scope()
            if node.else_body:
                push_with_label("if-else")
                for s in node.else_body: visit(s)
                analyzer.sym.pop_scope()

    for stmt in program.statements:
        visit(stmt)
    return rows


def draw_symbol_table(rows, title, out_path):
    fig, ax = plt.subplots(figsize=(10, max(2.5, 0.55 * len(rows) + 1.5)))
    ax.set_axis_off()
    ax.set_title(title, fontsize=14, weight="bold", pad=12)

    headers = ["Scope", "Name", "Kind", "Type", "Line"]
    if not rows:
        rows = [("global", "(none)", "—", "—", "—")]

    note = None
    if rows and rows[0][1] == "(none)":
        note = ("This program declares no variables or palettes,\n"
                "so the symbol table is empty. CANVAS, RECT, FILL\n"
                "and SAVE are statements (not symbols) and do not\n"
                "appear in the table by design.")
    table_data = [headers] + [list(map(str, r)) for r in rows]
    n_rows = len(table_data)
    n_cols = len(headers)

    col_widths = [0.20, 0.22, 0.18, 0.20, 0.12]
    cell_h = 1.0 / n_rows

    for i, row in enumerate(table_data):
        y = 1.0 - (i + 1) * cell_h
        x = 0.04
        for j, val in enumerate(row):
            w = col_widths[j] * 0.92
            is_header = i == 0
            fc = "#3367C9" if is_header else ("#F5F8FF" if i % 2 == 0 else "#FFFFFF")
            tc = "white" if is_header else "#222"
            ax.add_patch(FancyBboxPatch((x, y), w, cell_h,
                                        boxstyle="round,pad=0.005",
                                        fc=fc, ec="#3367C9", lw=1.0,
                                        transform=ax.transAxes))
            ax.text(x + w / 2, y + cell_h / 2, val, ha="center", va="center",
                    fontsize=10, color=tc, weight="bold" if is_header else "normal",
                    transform=ax.transAxes)
            x += col_widths[j] * 0.92 + 0.005

    if note:
        ax.text(0.5, -0.15, note, ha="center", va="top",
                fontsize=10, color="#555", style="italic",
                transform=ax.transAxes)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    plt.savefig(out_path, dpi=140, bbox_inches="tight", pad_inches=0.4)
    plt.close(fig)


# ─── Driver ──────────────────────────────────────────────────────────────────

def process(pix_path, out_dir, base):
    src = open(pix_path).read()
    tokens = Lexer(src).tokenize()
    ast = Parser(tokens).parse()

    parse_path = os.path.join(out_dir, f"{base}_parse_tree.png")
    sym_path   = os.path.join(out_dir, f"{base}_symbol_table.png")
    dfa_path   = os.path.join(out_dir, f"{base}_dfa.png")

    draw_parse_tree(ast, f"Parse Tree — {base}.pix", parse_path)
    rows = collect_symbols(ast)
    draw_symbol_table(rows, f"Symbol Table — {base}.pix", sym_path)
    draw_dfa(dfa_path, f"Lexer DFA — applied while tokenising {base}.pix")
    print(f"  {base}:  {parse_path}")
    print(f"            {sym_path}")
    print(f"            {dfa_path}")


def main():
    out_dir = os.path.join(ROOT, "diagrams")
    os.makedirs(out_dir, exist_ok=True)
    print(f"Writing diagrams to {out_dir}/")
    for base in ("test1_concentric", "test2_flag"):
        pix = os.path.join(ROOT, "tests", f"{base}.pix")
        process(pix, out_dir, base)


if __name__ == "__main__":
    main()
