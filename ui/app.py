import io
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))

import streamlit as st

from lexer        import Lexer, LexerError
from parser       import Parser, ParseError
from semantic     import SemanticAnalyzer, SemanticError
from ir_generator import IRGenerator
from optimizer    import Optimizer
from codegen      import VirtualMachine, CodegenError

st.set_page_config(page_title="PixLang Playground", layout="wide")
st.title("PixLang Playground")

DEFAULT = """CANVAS 64 64
PALETTE retro: #1A1C2C, #5D275D, #B13E53, #EF7D57, #FFCD75, #A7F070
FILL #1A1C2C
VAR size = 60
VAR col = 1
LOOP WHILE size > 4:
    RECT (32 - size / 2), (32 - size / 2), size, size, retro[col]
    size = size - 8
    col = (col + 1) MOD 6
ENDLOOP
CIRCLE 32 32 RADIUS 6 COLOR retro[5]
SAVE "out.png"
"""

left, right = st.columns(2)

with left:
    src = st.text_area("Source (.pix)", DEFAULT, height=520)
    show_ir = st.checkbox("Show intermediate phases", value=False)
    run = st.button("Compile", type="primary")

with right:
    if run:
        try:
            tokens    = Lexer(src).tokenize()
            ast       = Parser(tokens).parse()
            SemanticAnalyzer().analyze(ast)
            ir_gen    = IRGenerator()
            raw_ir    = ir_gen.generate(ast)
            optimized, before, after = Optimizer(raw_ir).optimize()
            vm = VirtualMachine()
            vm.execute(optimized)
        except (LexerError, ParseError, SemanticError, CodegenError) as e:
            st.error(str(e))
        else:
            if vm.image is None:
                st.warning("No CANVAS produced an image.")
            else:
                buf = io.BytesIO()
                vm.image.save(buf, format="PNG")
                st.image(buf.getvalue(), caption=f"{vm.width}x{vm.height}")
                st.download_button("Download PNG", buf.getvalue(),
                                   file_name="output.png", mime="image/png")
            st.caption(f"Optimizer: {before} -> {after} instructions "
                       f"({before - after} removed)")
            if show_ir:
                with st.expander("Tokens"):
                    st.code("\n".join(f"{t.type:12s} {t.value!r:25s} L{t.line}:C{t.col}"
                                      for t in tokens if t.type != 'EOF'))
                with st.expander("Three-Address Code (optimised)"):
                    st.code(Optimizer.pretty_print(optimized))
    else:
        st.info("Edit the source on the left and press Compile.")
