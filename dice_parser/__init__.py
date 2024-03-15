import operator
import typing
from dataclasses import dataclass
from typing import Callable

from lark import Lark, Transformer, v_args

from dice_parser.dice_roller import (
    DiceRoller,
    HighestDiceModifier,
    DiceModifier,
    NullDiceModifier,
    LowestDiceModifier,
)

ParserResultT = typing.TypeVar('ParserResultT', bound='_ParseResult')


class OperatorCallableResultT(typing.Protocol):
    def __call__(self, *args: '_ParseResult') -> '_ParseResult':
        ...


@dataclass
class ParseResult:
    value: int
    string: str


class _ParseResult:
    def __init__(
        self,
        value: int | DiceModifier,
        string: str | None,
        flag: str | None = None,
    ) -> None:
        self.value: int | DiceModifier = value
        self.string: str | None = string
        self.flag: str | None = flag

    def to_public_result(self) -> ParseResult:
        assert isinstance(self.value, int)
        assert isinstance(self.string, str)
        return ParseResult(self.value, self.string)

    def __repr__(self) -> str:
        return '{}({}, {}, {})'.format(
            type(self).__name__,
            repr(self.value),
            repr(self.string),
            repr(self.flag)
        )

    @classmethod
    def operator(
        cls: type[ParserResultT],
        operator_callable: typing.Any,
        template: str,
    ) -> Callable[[typing.Any], OperatorCallableResultT]:
        @v_args(inline=True)
        def result(decorated_self: typing.Any, *args: _ParseResult) -> _ParseResult:
            return cls(
                operator_callable(*(x.value for x in args)),
                template.format(*(x.string for x in args)),
            )

        return result


class DiceTransformer(Transformer[_ParseResult, int]):
    def __init__(self) -> None:
        super().__init__()
        self.vars: dict[str, _ParseResult] = {}

    add = _ParseResult.operator(operator.add, '{} + {}')
    sub = _ParseResult.operator(operator.sub, '{} - {}')
    mul = _ParseResult.operator(operator.mul, '{} * {}')
    div = _ParseResult.operator(operator.floordiv, '{} / {}')
    neg = _ParseResult.operator(operator.neg, '-{}')

    @v_args(inline=True)
    def number(self, value: str) -> _ParseResult:
        return _ParseResult(int(value), str(int(value)), None)

    @v_args(inline=True)
    def dice_count(self, result: _ParseResult) -> _ParseResult:
        return self._add_flag(result, 'dice_count')

    @v_args(inline=True)
    def dice_size(self, result: _ParseResult) -> _ParseResult:
        assert isinstance(result.value, int)
        if result.value < 1:
            result.value = 0
        return self._add_flag(result, 'dice_size')

    @v_args(inline=True)
    def dice_highest(self, result: _ParseResult) -> _ParseResult:
        assert isinstance(result.value, int)
        return _ParseResult(HighestDiceModifier(int(result.value)), None, 'dice_modifier')

    @v_args(inline=True)
    def dice_lowest(self, result: _ParseResult) -> _ParseResult:
        assert isinstance(result.value, int)
        return _ParseResult(LowestDiceModifier(int(result.value)), None, 'dice_modifier')

    @v_args(inline=True)
    def brackets(self, result: _ParseResult) -> _ParseResult:
        return _ParseResult(result.value, '({})'.format(result.string))

    @v_args(inline=True)
    def roll(self, *args: _ParseResult) -> _ParseResult:
        count = 1
        size = 20
        modifier: DiceModifier = NullDiceModifier()
        for arg in args:
            if arg.flag == 'dice_count':
                assert isinstance(arg.value, int)
                count = arg.value
            if arg.flag == 'dice_size':
                assert isinstance(arg.value, int)
                size = arg.value
            if arg.flag == 'dice_modifier':
                assert isinstance(arg.value, DiceModifier)
                modifier = arg.value

        roller = DiceRoller(count, size, modifier)
        rolled_result, rolled_dice = roller.roll()

        return _ParseResult(
            rolled_result,
            '[{}]'.format(', '.join(str(d) for d in rolled_dice)),
        )

    @v_args(inline=True)
    def assign_var(self, name: str, result: _ParseResult) -> _ParseResult:
        self.vars[name] = _ParseResult(
            result.value,
            name,
        )

        return _ParseResult(
            result.value,
            '{} = {}'.format(name, result.string),
        )

    @v_args(inline=True)
    def var(self, name: str) -> _ParseResult:
        return self.vars[name]

    @classmethod
    def _add_flag(cls, result: _ParseResult, flag: str) -> _ParseResult:
        return _ParseResult(result.value, result.string, flag)


class DiceParser:
    GRAMMAR = """
        NAME: /[a-z_]+/
        NUMBER: /\\d+/

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

    def __init__(self) -> None:
        self._parser = Lark(self.GRAMMAR, parser='lalr', transformer=DiceTransformer())

    def parse(self, string: str) -> ParseResult:
        result = self._parser.parse(string)
        assert isinstance(result, _ParseResult)

        return result.to_public_result()
