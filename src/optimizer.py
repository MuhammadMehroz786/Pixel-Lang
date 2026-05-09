class Optimizer:
    def __init__(self, instructions):
        self.instructions = list(instructions)

    def optimize(self):
        before = len(self.instructions)
        self.instructions = self._constant_folding(self.instructions)
        self.instructions = self._dead_variable_elimination(self.instructions)
        after = len(self.instructions)
        return self.instructions, before, after

    def _constant_folding(self, instrs):
        result = []
        for instr in instrs:
            op = instr[0]

            if op == 'BINOP':
                dest, left, op_sym, right = instr[1], instr[2], instr[3], instr[4]
                if isinstance(left, (int, float)) and isinstance(right, (int, float)):
                    folded = self._eval_binop(left, op_sym, right)
                    if folded is not None:
                        result.append(('ASSIGN', dest, folded, None))
                        continue
                result.append(instr)

            elif op == 'UNARY':
                dest, op_sym, operand = instr[1], instr[2], instr[3]
                if isinstance(operand, (int, float)) and op_sym == '-':
                    result.append(('ASSIGN', dest, -operand, None))
                    continue
                result.append(instr)

            else:
                result.append(instr)

        return result

    def _eval_binop(self, left, op, right):
        try:
            if op == '+':   return left + right
            if op == '-':   return left - right
            if op == '*':   return left * right
            if op == '/':
                if right == 0: return None
                return left // right if isinstance(left, int) and isinstance(right, int) else left / right
            if op == 'MOD': return int(left) % int(right)
            if op == '<':   return int(left < right)
            if op == '>':   return int(left > right)
            if op == '<=':  return int(left <= right)
            if op == '>=':  return int(left >= right)
            if op == '==':  return int(left == right)
            if op == '!=':  return int(left != right)
        except Exception:
            pass
        return None

    def _dead_variable_elimination(self, instrs):
        used = self._collect_all_sources(instrs)
        result = []
        for instr in instrs:
            op = instr[0]
            if op in ('ASSIGN', 'BINOP', 'UNARY', 'PALETTE_IDX'):
                dest = instr[1]
                if self._is_temp(dest) and dest not in used:
                    continue
            result.append(instr)
        return result

    def _is_temp(self, name):
        return (isinstance(name, str)
                and len(name) >= 2
                and name[0] == 't'
                and name[1:].isdigit())

    def _collect_all_sources(self, instrs):
        used = set()
        for instr in instrs:
            op = instr[0]
            if op in ('ASSIGN', 'BINOP', 'UNARY', 'PALETTE_IDX'):
                for item in instr[2:]:
                    self._collect(item, used)
            elif op == 'JUMPF':
                self._collect(instr[1], used)
            elif op in ('RECT', 'CIRCLE', 'LINE', 'PIXEL'):
                self._collect(instr[1], used)
            elif op == 'FILL':
                self._collect(instr[1], used)
            elif op == 'CANVAS':
                self._collect(instr[1], used)
                self._collect(instr[2], used)
        return used

    def _collect(self, item, used):
        if isinstance(item, str):
            used.add(item)
        elif isinstance(item, (list, tuple)):
            for sub in item:
                if isinstance(sub, str):
                    used.add(sub)

    @staticmethod
    def pretty_print(instrs):
        from ir_generator import IRGenerator
        tmp = IRGenerator.__new__(IRGenerator)
        tmp.instructions = instrs
        return tmp.pretty_print()
