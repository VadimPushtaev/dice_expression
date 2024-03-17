import operator

from lark import Transformer, v_args

from dice_parser.dice_roller import DiceRoller
from dice_parser.modifier import DiceModifier
from dice_parser.parser_result import InternalParseResult


class NullDiceModifier(DiceModifier):
    def get_actual_dice(self, dice: list[int]) -> tuple[list[int], list[int]]:
        return dice, []


class HighestDiceModifier(DiceModifier):
    def get_actual_dice(self, dice: list[int]) -> tuple[list[int], list[int]]:
        sorted_dice = sorted(dice)
        count = self._safe_count(dice)
        n = len(sorted_dice)

        return sorted_dice[n - count:], sorted_dice[:n - count]


class LowestDiceModifier(DiceModifier):
    def get_actual_dice(self, dice: list[int]) -> tuple[list[int], list[int]]:
        sorted_dice = sorted(dice)
        count = self._safe_count(dice)

        return sorted_dice[:count], sorted_dice[count:]


class DiceTransformer(Transformer[InternalParseResult, int]):
    def __init__(self) -> None:
        super().__init__()
        self.vars: dict[str, InternalParseResult] = {}

    add = InternalParseResult.operator(operator.add, '{} + {}')
    sub = InternalParseResult.operator(operator.sub, '{} - {}')
    mul = InternalParseResult.operator(operator.mul, '{} * {}')
    div = InternalParseResult.operator(operator.floordiv, '{} / {}')
    neg = InternalParseResult.operator(operator.neg, '-{}')

    @v_args(inline=True)
    def number(self, value: str) -> InternalParseResult:
        return InternalParseResult(int(value), str(int(value)), None)

    @v_args(inline=True)
    def dice_count(self, result: InternalParseResult) -> InternalParseResult:
        return self._add_flag(result, 'dice_count')

    @v_args(inline=True)
    def dice_size(self, result: InternalParseResult) -> InternalParseResult:
        assert isinstance(result.value, int)
        if result.value < 1:
            result.value = 0
        return self._add_flag(result, 'dice_size')

    @v_args(inline=True)
    def dice_highest(self, result: InternalParseResult) -> InternalParseResult:
        assert isinstance(result.value, int)
        return InternalParseResult(HighestDiceModifier(int(result.value)), None, 'dice_modifier')

    @v_args(inline=True)
    def dice_lowest(self, result: InternalParseResult) -> InternalParseResult:
        assert isinstance(result.value, int)
        return InternalParseResult(LowestDiceModifier(int(result.value)), None, 'dice_modifier')

    @v_args(inline=True)
    def brackets(self, result: InternalParseResult) -> InternalParseResult:
        return InternalParseResult(result.value, '({})'.format(result.string))

    @v_args(inline=True)
    def roll(self, *args: InternalParseResult) -> InternalParseResult:
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

        return InternalParseResult(
            rolled_result,
            '[{}]'.format(', '.join(str(d) for d in rolled_dice)),
        )

    @v_args(inline=True)
    def assign_var(self, name: str, result: InternalParseResult) -> InternalParseResult:
        self.vars[name] = InternalParseResult(
            result.value,
            name,
        )

        return InternalParseResult(
            result.value,
            '{} = {}'.format(name, result.string),
        )

    @v_args(inline=True)
    def var(self, name: str) -> InternalParseResult:
        return self.vars[name]

    @classmethod
    def _add_flag(cls, result: InternalParseResult, flag: str) -> InternalParseResult:
        return InternalParseResult(result.value, result.string, flag)
