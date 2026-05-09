try:
    from PIL import Image, ImageDraw
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False


class CodegenError(Exception):
    def __init__(self, message):
        super().__init__(f"[Codegen Error]: {message}")


class VirtualMachine:
    def __init__(self):
        self.registers   = {}
        self.palettes    = {}
        self.image       = None
        self.draw        = None
        self.width       = 0
        self.height      = 0
        self.saved_files = []

    def execute(self, instructions):
        if not PILLOW_AVAILABLE:
            raise CodegenError("Pillow not installed. Run: pip install Pillow")

        for instr in instructions:
            if instr[0] == 'CANVAS':
                self._init_canvas(int(self._resolve(instr[1])),
                                  int(self._resolve(instr[2])))
                break

        pc        = 0
        label_map = self._build_label_map(instructions)

        while pc < len(instructions):
            instr = instructions[pc]
            op    = instr[0]

            if op == 'CANVAS':
                self._init_canvas(int(self._resolve(instr[1])),
                                  int(self._resolve(instr[2])))

            elif op == 'PALETTE':
                self.palettes[instr[1]] = instr[2]

            elif op == 'PALETTE_IDX':
                dest, pname, idx = instr[1], instr[2], instr[3]
                idx_v   = int(self._resolve(idx))
                palette = self.palettes.get(pname)
                if palette is None:
                    raise CodegenError(f"Undefined palette '{pname}'")
                self.registers[dest] = palette[idx_v % len(palette)]

            elif op == 'ASSIGN':
                self.registers[instr[1]] = self._resolve(instr[2])

            elif op == 'BINOP':
                dest, left, op_sym, right = instr[1], instr[2], instr[3], instr[4]
                lv = self._resolve(left)
                rv = self._resolve(right)
                self.registers[dest] = self._eval(lv, op_sym, rv)

            elif op == 'UNARY':
                dest, op_sym, operand = instr[1], instr[2], instr[3]
                v = self._resolve(operand)
                self.registers[dest] = -v if op_sym == '-' else v

            elif op == 'FILL':
                self._require_canvas()
                color = self._parse_color(self._resolve(instr[1]))
                self.draw.rectangle([0, 0, self.width-1, self.height-1], fill=color)

            elif op == 'RECT':
                x, y, w, h, c = instr[1]
                xv = int(self._resolve(x))
                yv = int(self._resolve(y))
                wv = int(self._resolve(w))
                hv = int(self._resolve(h))
                cv = self._parse_color(self._resolve(c))
                self._require_canvas()
                self.draw.rectangle([xv, yv, xv+wv-1, yv+hv-1], fill=cv)

            elif op == 'CIRCLE':
                cx, cy, r, c = instr[1]
                cxv = int(self._resolve(cx))
                cyv = int(self._resolve(cy))
                rv  = int(self._resolve(r))
                cv  = self._parse_color(self._resolve(c))
                self._require_canvas()
                self.draw.ellipse([cxv-rv, cyv-rv, cxv+rv, cyv+rv], fill=cv)

            elif op == 'LINE':
                x1, y1, x2, y2, c = instr[1]
                cv = self._parse_color(self._resolve(c))
                self._require_canvas()
                self.draw.line([int(self._resolve(x1)), int(self._resolve(y1)),
                                int(self._resolve(x2)), int(self._resolve(y2))],
                               fill=cv, width=1)

            elif op == 'PIXEL':
                x, y, c = instr[1]
                cv = self._parse_color(self._resolve(c))
                self._require_canvas()
                self.image.putpixel((int(self._resolve(x)), int(self._resolve(y))), cv)

            elif op == 'SAVE':
                self._require_canvas()
                self.image.save(instr[1])
                self.saved_files.append(instr[1])
                print(f"  [CodeGen] Saved: {instr[1]}")

            elif op == 'LABEL':
                pass

            elif op == 'JUMP':
                pc = label_map[instr[1]]
                continue

            elif op == 'JUMPF':
                cond_v = self._resolve(instr[1])
                if not cond_v:
                    pc = label_map[instr[2]]
                    continue

            pc += 1

        return self.saved_files

    def _init_canvas(self, w, h):
        self.width  = w
        self.height = h
        self.image  = Image.new('RGB', (w, h), (0, 0, 0))
        self.draw   = ImageDraw.Draw(self.image)

    def _require_canvas(self):
        if self.image is None:
            raise CodegenError("No CANVAS initialised before drawing command")

    def _resolve(self, val):
        if isinstance(val, str) and not val.startswith('#') and val in self.registers:
            return self.registers[val]
        return val

    def _eval(self, left, op, right):
        if op == '+':   return left + right
        if op == '-':   return left - right
        if op == '*':   return left * right
        if op == '/':
            if right == 0:
                raise CodegenError("Division by zero")
            if isinstance(left, int) and isinstance(right, int):
                return left // right
            return left / right
        if op == 'MOD': return int(left) % int(right)
        if op == '<':   return int(left < right)
        if op == '>':   return int(left > right)
        if op == '<=':  return int(left <= right)
        if op == '>=':  return int(left >= right)
        if op == '==':  return int(left == right)
        if op == '!=':  return int(left != right)
        raise CodegenError(f"Unknown operator: {op}")

    def _parse_color(self, color_str):
        if not isinstance(color_str, str) or not color_str.startswith('#'):
            raise CodegenError(f"Invalid color value: {color_str!r}")
        h = color_str.lstrip('#')
        if len(h) == 3:
            h = h[0]*2 + h[1]*2 + h[2]*2
        if len(h) != 6:
            raise CodegenError(f"Invalid hex color: #{h}")
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))

    def _build_label_map(self, instructions):
        lm = {}
        for i, instr in enumerate(instructions):
            if instr[0] == 'LABEL':
                lm[instr[1]] = i
        return lm
