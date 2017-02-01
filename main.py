import dis
import builtins
import sys
import types
import inspect
import operator


class Frame(object):
    def __init__(self):
        self.data_stack = []
        self.block_stack = []
        self.locals = dict()
        self.noname_locals = dict()


class Function(object):  # INCOMPLETE

    def __init__(self, qualname, codeobject, vm, defaults):
        self.__qualname__ = qualname
        self.__name__ = qualname
        self.codeobject = codeobject
        self.vm = vm
        self.func_ = types.FunctionType(self.codeobject, globals(),
                                        self.__qualname__, defaults)

    def __repr__(self):
        return '<Function %s at 0x{:08d}>'.format(self.__name__, id(self))

    def __call__(self, *args, **kwargs):
        self.frame = Frame()
        prepared_args = inspect.getcallargs(self.func_, *args, **kwargs)
        self.frame.locals = dict(prepared_args)
        return self.vm.run_function(self)

    def clean_up(self):
        pass


class Executor(object):

    def __init__(self, instruction, frame, instructions, vm):
        self.stack = frame.data_stack
        self.frame = frame
        self.argval = instruction.argval
        self.locals_ = frame.locals
        self.block_stack = frame.block_stack
        self.instructions = instructions
        self.vm_ = vm

    def NOP(self):  # No Instruction mehtods
        return

    def POP_TOP(self):
        self.stack.pop()

    def ROT_TWO(self):
        self.stack[-2], self.stack[-1] = self.stack[-1], self.stack[-2]

    def ROT_THREE(self):
        self.stack[-3], self.stack[-2], self.stack[-1] = self.stack[-1],\
                                                         self.stack[-3],\
                                                         self.stack[-2]

    def DUP_TOP(self):
        self.stack.append(self.stack[-1])

    def DUP_TOP_TWO(self):
        self.stack.append(self.stack[-2])
        self.stack.append(self.stack[-2])

    def STORE_SUBSCR(self):  # MAYBE WRONG
        a = self.stack[-1]
        self.stack.pop()
        b = self.stack[-1]
        self.stack.pop()
        c = self.stack[-1]
        self.stack.pop()
        b[a] = c

    def DELETE_SUBSCR(self):  # MAYBE WRONG
        a = self.stack[-1]
        self.stack.pop()
        b = self.stack[-1]
        self.stack.pop()
        del b[a]

    def PRINT_EXPR(self):  # MAYBE WRONG
        print(self.stack.pop())

    def LOAD_BUILD_CLASS(self):
        self.stack.append(builtins.__build_class__())

    def UNPACK_SEQUENCE(self):
        TOS = self.stack[-1]
        self.stack.pop()
        for x in reversed(TOS):
                self.stack.append(x)

    def STORE_MAP(self):
        map_, val, key = self.stack[-3:]
        self.stack[-2:] = []
        map_[key] = val

    def LOAD_GLOBAL(self):
        if self.argval in globals():
            self.stack.append(globals()[self.argval])
        else:
            self.stack.append(getattr(builtins, self.argval))

    def LOAD_NAME(self):  # INCOMPLETE
        if self.argval in self.locals_:
            self.stack.append(self.locals_[self.argval])
        elif self.argval in globals():
            self.stack.append(globals()[self.argval])
        elif self.argval in dir(builtins):
            self.stack.append(getattr(builtins, self.argval))
        else:
            raise NameError()

    def LOAD_FAST(self):
        if self.argval in self.locals_:
            self.stack.append(self.locals_[self.argval])
        else:
            raise NameError()

    def STORE_GLOBAL(self):
        globals()[self.argval] = self.stack.pop()

    def STORE_NAME(self):  # MAYBE WRONG
        self.locals_[self.argval] = self.stack[-1]
        self.stack.pop()

    def STORE_FAST(self):
        self.locals_[self.argval] = self.stack[-1]
        self.stack.pop()

    def DELETE_NAME(self):
        if instruction.argval in self.locals_:
            del locals_[self.argval]
        else:
            del globals()[self.argval]

    def DELETE_FAST(self):
        del self.locals_[self.argval]

    def DELETE_GLOBAL(self):
        del globals()[self.argval]

    def CONTINUE_LOOP(self):
        return self.instructions[self.argval]

    def SET_ADD(self):
        a = self.stack[-1]
        self.stack.pop()
        self.stack[-self.argval].add(a)

    def LIST_APPEND(self):
        value = self.stack[-1]
        self.stack.pop()
        key = self.stack[-1]
        self.stack.pop()
        self.stack[-self.argval][key] = value

    def MAP_ADD(self):
        a = self.stack[-1]
        self.stack[-self.argval] = a

    def RETURN_VALUE(self):
        a = self.stack[-1]
        self.stack.pop()
        return (a,)

    def POP_BLOCK(self):
        self.block_stack.pop()

    def STORE_ATTR(self):  # need tests
        a = self.stack[-1]
        self.stack.pop()
        b = self.stack[-1]
        self.stack.pop()
        setattr(a, self.argval, b)

    def DELETE_ATTR(self):  # need tests
        a = self.stack[-1]
        self.stack.pop()
        delattr(a, self.argval)

    def JUMP_FORWARD(self):  # MAYBE WRONG NEW!!!!!!!!!!!!!!!!
        return self.instructions[self.argval]

    def POP_JUMP_IF_TRUE(self):
        a = self.stack.pop()
        if a:
            return instructions[self.argval]

    def POP_JUMP_IF_FALSE(self):
        a = self.stack.pop()
        if not a:
            return self.instructions[self.argval]

    def JUMP_IF_TRUE_OR_POP(self):
        a = self.stack[-1]
        if a:
            return self.instructions[self.argval]
        else:
            self.stack.pop()

    def JUMP_IF_FALSE_OR_POP(self):
        a = self.stack[-1]
        if not a:
            return self.instructions[self.argval]
        else:
            self.stack.pop()

    def JUMP_ABSOLUTE(self):
        return self.instructions[self.argval]

    def FOR_ITER(self):
        TOS = self.stack[-1]
        try:
            a = next(TOS)
            self.stack.append(a)
        except StopIteration:
            self.stack.pop()
            return self.instructions[self.argval]

    def SETUP_LOOP(self):
        self.block_stack.append(('loop', self.argval))

    def BREAK_LOOP(self):
        index = self.instructions[self.block_stack[-1][1]]
        self.block_stack.pop()
        return index

    def LOAD_CONST(self):
        self.stack.append(self.argval)

    def BUILD_TUPLE(self):
        args = []
        for i in range(self.argval):
            args.append(self.stack.pop())
        args = reversed(args)
        self.stack.append(tuple(args))

    def BUILD_LIST(self):
        args = []
        for i in range(self.argval):
            args.append(self.stack[-1].pop())
        args = reversed(args)
        self.stack.append(list(args))

    def BUILD_SET(self):
        args = []
        for i in range(self.argval):
            args.append(self.stack[-1])
            self.stack.pop()
        args = reversed(args)
        stack.append(set(args))

    def BUILD_MAP(self):
        args = []
        for i in range(self.argval):
            args.append((self.stack[-2], self.stack[-1]))
            self.stack.pop()
            self.stack.pop()
        self.stack.append(dict(args))

    def LOAD_ATTR(self):
        self.stack[-1] = getattr(self.stack[-1], self.argval)

    def FOR_ITER(self):
        TOS = self.stack[-1]
        try:
            a = next(TOS)
            self.stack.append(a)
        except StopIteration:
            self.stack.pop()
            return self.instructions[self.argval]

    def CALL_FUNCTION(self):
        pos_args_number = self.argval % 256
        keyword_args_number = self.argval // 256
        keyword_args = {}
        for i in range(keyword_args_number):
            keyword_args[self.stack[-2]] = self.stack[-1]
            self.stack.pop()
            self.stack.pop()
        pos_args = []
        for i in range(pos_args_number):
            pos_args.append(self.stack[-1])
            self.stack.pop()
        pos_args = reversed(pos_args)
        function = self.stack[-1]
        self.stack.pop()
        self.stack.append(function(*pos_args, **keyword_args))

    def MAKE_FUNCTION(self):  # INCOMPLETE
        qualname = self.stack[-1]
        self.stack.pop()
        codeobject = self.stack[-1]
        self.stack.pop()
        defaults_num = self.argval & 0xFF
        named_defaults_num = (self.argval >> 8) & 0xFF
        annotation_num = (self.argval >> 16) & 0x7FFF
        defaults = []
        for i in range(defaults_num):
            defaults.append(self.stack[-1])
            self.stack.pop()
        self.stack.append(Function(qualname, codeobject,
                                   self.vm_, tuple(defaults)))

    def BUILD_SLICE(self):
        if self.argval == 2:
            b, a = self.stack[-2:]
            self.stack[-2:] = []
            self.stack.append(slice(b, a))
        else:
            c, b, a = self.stack[-3:]
            self.stack[-3:] = []
            self.stack.append(slice(c, b, a))

    def UNARY_POSITIVE(self):
            self.stack[-1] = +self.stack[-1]

    def UNARY_NEGATIVE(self):
            self.stack[-1] = -self.stack[-1]

    def UNARY_NOT(self):
            self.stack[-1] = not self.stack[-1]

    def UNARY_INVERT(self):
        self.stack[-1] = ~self.stack[-1]

    def GET_ITER(self):
        self.stack[-1] = iter(self.stack[-1])

    def COMPARE_OP(self):  # exception match and BAD?
        a = self.stack[-1]
        self.stack.pop()
        b = self.stack[-1]
        self.stack.pop()
        operators = {
            '<': operator.lt,
            '<=': operator.le,
            '>': operator.gt,
            '>=': operator.ge,
            '==': operator.eq,
            '!=': operator.ne,
            'is': operator.is_,
            'is not': operator.is_not,
            'in': lambda x, y: x in y,
            'not in': lambda x, y: x not in y
        }
        self.stack.append(operators[self.argval](b, a))


class VirtualMachine(object):
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.call_stack = [Frame()]

    def prepare_codeobject_(self, codeobject):
        instructions = dict()
        instructions_list = []
        for instruction in dis.get_instructions(codeobject):
            instructions[instruction.offset] = len(instructions_list)
            instructions_list.append(instruction)
        return instructions, instructions_list

    def execute(self, instruction, instructions):
        stack = self.call_stack[-1].data_stack
        executor = Executor(instruction, self.call_stack[-1],
                            instructions, self)
        if 'BINARY' in instruction.opname:
            a = stack.pop()
            b = stack.pop()
            operations = {
                'BINARY_POWER': operator.pow,
                'BINARY_MULTIPLY': operator.mul,
                'BINARY_FLOOR_DIVIDE': operator.floordiv,
                'BINARY_TRUE_DIVIDE': operator.truediv,
                'BINARY_MODULO': operator.mod,
                'BINARY_ADD': operator.add,
                'BINARY_SUBSTRACT': operator.sub,
                'BINARY_SUBSCR': operator.getitem,
                'BINARY_LSHIFT': operator.lshift,
                'BINARY_RSHIFT': operator.rshift,
                'BINARY_AND': operator.and_,
                'BINARY_XOR': operator.xor,
                'BINARY_OR': operator.or_,
            }
            stack.append(operations[instruction.opname](b, a))
        elif 'INPLACE' in instruction.opname:
            a = stack[-1]
            stack.pop()
            operations = {
                'INPLACE_POWER': operator.ipow,
                'INPLACE_MULTIPLY': operator.imul,
                'INPLACE_FLOOR_DIVIDE': operator.ifloordiv,
                'INPLACE_TRUE_DIVIDE': operator.itruediv,
                'INPLACE_MODULO': operator.imod,
                'INPLACE_ADD': operator.iadd,
                'INPLACE_SUBTRACT': operator.isub,
                'INPLACE_LSHIFT': operator.ilshift,
                'INPLACE_RSHIFT': operator.irshift,
                'INPLACE_AND': operator.iand,
                'INPLACE_XOR': operator.ixor,
                'INPLACE_OR': operator.ior,
            }
            stack[-1] = operations[instruction.opname](stack[-1], a)
        elif instruction.opname in dir(Executor):
            return getattr(executor, instruction.opname)()

    def run_code(self, codeobject):
        if type(codeobject) == str:
            codeobject = compile(codeobject, '', 'exec')
        self.__init__(self.verbose)
        instructions, instructions_list = self.prepare_codeobject_(codeobject)
        index = 0
        while index != len(instructions_list):
            execute_return = self.execute(instructions_list[index],
                                          instructions)
            while type(execute_return) is int:
                index = execute_return
                execute_return = self.execute(instructions_list[index],
                                              instructions)
            index += 1
        if self.verbose:
            print('END EXECUTION.\t\t STACK IS',
                  self.call_stack[-1].data_stack)

    def run_function(self, function):
        self.call_stack.append(function.frame)
        instructions, instructions_list = self.prepare_codeobject_(
                                                        function.codeobject)
        index = 0
        while index != len(instructions_list):
            execute_return = self.execute(instructions_list[index],
                                          instructions)
            while type(execute_return) is int:
                index = execute_return
                execute_return = self.execute(instructions_list[index],
                                              instructions)
            if type(execute_return) is tuple:
                function.clean_up()
                self.call_stack.pop()
                return execute_return[0]
            index += 1
        if self.verbose:
            print('END EXECUTION.\t\t STACK IS',
                  self.call_stack[-1].data_stack)


if __name__ == "__main__":
    compiled = compile(sys.stdin.read(), "<stdin>", 'exec')
    VirtualMachine().run_code(compiled)
