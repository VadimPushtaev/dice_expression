from unittest import TestCase

from dice_parser.dice_roller import DiceRoller
from dice_parser.parser import DiceParser


class DiceExpressionTestCase(TestCase):
    def setUp(self):
        self.parser = DiceParser()
        DiceRoller._roll_die = lambda cls_, size: size

    def test_simple(self):
        result = self.parser.parse('3*4 + 12/3 + ( 3-2 )')
        self.assertEqual(17, result.value)
        self.assertEqual('3 * 4 + 12 / 3 + (3 - 2)', result.string)

    def test_dice(self):
        result = self.parser.parse('d10 * 3 + 2D + ( 3 D 30 )')
        self.assertEqual(160, result.value)
        self.assertEqual('[10] * 3 + [20, 20] + ([30, 30, 30])', result.string)

    def test_dice__invalid_size(self):
        result = self.parser.parse('3d0')
        self.assertEqual(0, result.value)
        self.assertEqual('[0, 0, 0]', result.string)
        result = self.parser.parse('2d(-1)')
        self.assertEqual(0, result.value)
        self.assertEqual('[0, 0]', result.string)

    def test_dice__invalid_count(self):
        result = self.parser.parse('0d3')
        self.assertEqual(0, result.value)
        self.assertEqual('[]', result.string)
        result = self.parser.parse('(-3)d3')
        self.assertEqual(0, result.value)
        self.assertEqual('[]', result.string)

    def test_dice__dynamic(self):
        result = self.parser.parse('(2+2) d (3*3)+1')
        self.assertEqual(37, result.value)
        self.assertEqual('[9, 9, 9, 9] + 1', result.string)

    def test_dice__modifier(self):
        rolled = iter([
            1, 6, 5, 4, 3, 2, # 6d6
            1,                # L(1d20)
            20, 15            # 2d20
        ])
        DiceRoller._roll_die = lambda cls_, size: next(rolled)

        result = self.parser.parse('6d6h3 + 2d20L(1d1)')
        self.assertEqual(30, result.value)
        self.assertEqual('[1, 6, 5, 4, 3, 2] + [20, 15]', result.string)

    def test_dice__strange_modifier(self):
        self.assertEqual(self.parser.parse('3d10H5').value, 30)
        self.assertEqual(self.parser.parse('3d10H0').value, 0)
        self.assertEqual(self.parser.parse('3d10H(-1)').value, 0)
        self.assertEqual(self.parser.parse('3d10L5').value, 30)
        self.assertEqual(self.parser.parse('3d10L0').value, 0)
        self.assertEqual(self.parser.parse('3d10L(-1)').value, 0)

    def test_vars(self):
        result = self.parser.parse('a=2+2')
        self.assertEqual(4, result.value)
        self.assertEqual('a = 2 + 2', result.string)

        result = self.parser.parse('d a')
        self.assertEqual(4, result.value)
        self.assertEqual('[4]', result.string)

