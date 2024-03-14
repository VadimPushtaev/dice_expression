import operator
from functools import wraps

from lark import Lark, Transformer, v_args

from dice_parser.dice_roller import DiceRoller, HighestDiceModifier, DiceModifier, NullDiceModifier, LowestDiceModifier


class ParseResult:
    def __init__(self, value, string, flag=None):
        self.value = value
        self.string = string
        self.flag = flag

    def __repr__(self):
        return '{}({}, {}, {})'.format(
            type(self).__name__,
            repr(self.value),
            repr(self.string),
            repr(self.flag)
        )

    @classmethod
    def operator(cls, operator_callable, template):
        def decorator(method):
            @wraps(method)
            @v_args(inline=True)
            def decorated(decorated_self, *args):
                return cls(
                    operator_callable(*(x.value for x in args)),
                    template.format(*(x.string for x in args)),
                )

            return decorated

        return decorator


class DiceTransformer(Transformer):
    def __init__(self):
        super().__init__()
        self.vars = {}

    @v_args(inline=True)
    def number(self, value):
        return ParseResult(int(value), str(int(value)), [])

    @ParseResult.operator(operator.add, '{} + {}')
    def add(self):
        pass

    @ParseResult.operator(operator.sub, '{} - {}')
    def sub(self):
        pass

    @ParseResult.operator(operator.mul, '{} * {}')
    def mul(self):
        pass

    @ParseResult.operator(operator.floordiv, '{} / {}')
    def div(self):
        pass

    @ParseResult.operator(operator.neg, '-{}')
    def neg(self):
        pass

    @v_args(inline=True)
    def dice_count(self, result):
        return self._add_flag(result, 'dice_count')

    @v_args(inline=True)
    def dice_size(self, result):
        if result.value < 1:
            result.value = 0
        return self._add_flag(result, 'dice_size')

    @v_args(inline=True)
    def dice_highest(self, result):
        return ParseResult(HighestDiceModifier(int(result.value)), None, 'dice_modifier')

    @v_args(inline=True)
    def dice_lowest(self, result):
        return ParseResult(LowestDiceModifier(int(result.value)), None, 'dice_modifier')

    @v_args(inline=True)
    def brackets(self, result):
        return ParseResult(result.value, '({})'.format(result.string))

    @v_args(inline=True)
    def roll(self, *args):
        count = 1
        size = 20
        modifier = NullDiceModifier()
        for arg in args:
            if arg.flag == 'dice_count':
                count = arg.value
            if arg.flag == 'dice_size':
                size = arg.value
            if arg.flag == 'dice_modifier':
                modifier = arg.value

        roller = DiceRoller(count, size, modifier)
        rolled_result, rolled_dice = roller.roll()

        return ParseResult(rolled_result, '[{}]'.format(', '.join(str(d) for d in rolled_dice)))

    @v_args(inline=True)
    def assign_var(self, name, result):
        self.vars[name] = ParseResult(
            result.value,
            name,
        )

        return ParseResult(
            result.value,
            '{} = {}'.format(name, result.string),
        )

    @v_args(inline=True)
    def var(self, name):
        return self.vars[name]

    @classmethod
    def _add_flag(cls, result, flag):
        return ParseResult(result.value, result.string, flag)


class DiceParser:
    GRAMMAR = """
        NAME: /[a-z_]+/
        NUMBER: /\d+/

        ?start: sum
            | NAME "=" sum     -> assign_var

        ?sum: product
            | sum "+" product  -> add
            | sum "-" product  -> sub

        ?product: dice
            | product "*" dice  -> mul
            | product "/" dice  -> div
        
        ?dice: atom
            | dice_count? ("d" | "D") dice_size? dice_modifier? -> roll

        ?atom: NUMBER          -> number
            | "-" atom         -> neg
            | NAME             -> var
            | "(" sum ")"      -> brackets

        ?dice_modifier: ("h" | "H") atom -> dice_highest
            | ("l" | "L") atom           -> dice_lowest

        dice_count: atom -> dice_count
        dice_size: atom -> dice_size
        
        %import common.WS_INLINE
        %ignore WS_INLINE
    """

    def __init__(self):
        self._parser = Lark(self.GRAMMAR, parser='lalr', transformer=DiceTransformer())

    def parse(self, string):
        return self._parser.parse(string)
