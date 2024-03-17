from abc import ABCMeta, abstractmethod


class DiceModifier(metaclass=ABCMeta):
    def __init__(self, count: int = 0) -> None:
        self._count: int = count

    def _safe_count(self, dice: list[int]) -> int:
        return min(max(0, self._count), len(dice))

    @abstractmethod
    def get_actual_dice(self, dice: list[int]) -> tuple[list[int], list[int]]:
        pass


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
