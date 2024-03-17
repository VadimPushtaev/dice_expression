# dice_parser
Arithmetic expressions with dice roll support

## Installation

`pip install dice_parser`

## Usage

```python
In[1]:
from dice_parser.parser import DiceParser

In[2]: parser = DiceParser()

In[3]: result = parser.parse('2d6 + 4')

In[4]: result
Out[4]: ParseResult(8, '[3, 1] + 4', None)

In[5]: result.value
Out[5]: 8
```
