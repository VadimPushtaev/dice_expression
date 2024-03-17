from lark import Lark

from dice_parser.parser_result import InternalParseResult, ParseResult
from dice_parser.transformer import DiceTransformer


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
        assert isinstance(result, InternalParseResult)

        return result.to_public_result()


