from random import randrange

from dice_parser.modifier import DiceModifier


class DiceRoller:
    def __init__(self, count: int, size: int, modifier: DiceModifier) -> None:
        self._count: int = count
        self._size: int = size
        self._modifier: DiceModifier = modifier

    def roll(self) -> tuple[int, list[int]]:
        rolled = [self._roll_die(self._size) for _ in range(self._count)]
        actual, ignored = self._modifier.get_actual_dice(rolled)

        return sum(actual), rolled

    @classmethod
    def _roll_die(cls, size: int) -> int:
        return randrange(1, 1 + size) if size > 0 else 0
