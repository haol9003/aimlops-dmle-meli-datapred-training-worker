"""This package contains all the commands to execute on each pipeline step.

Each command should be a callable object that receives the necessary parameters. For example:

```python
class MyCommand:
    def __init__(self, param1, param2):
        self.param1 = param1
        self.param2 = param2

    def __call__(self):
        print(self.param1, self.param2)
```

Feel free to reuse existing libraries like eliza-data and eliza-predict to implement the commands. For example:

```python
from eliza.data.readers import ParquetReader
from eliza.data.transforms import SequentialDataTransform
from eliza.data.transforms.tabular import DropDuplicates, DropNaRows


class ReadProductGroup:
    def __init__(self, data_path: str):
        self.data_path = data_path

    def __call__(self):
        reader = ParquetReader(self.data_path)
        transform = SequentialDataTransform(
            [
                DropNaRows("pg_name"),
                DropDuplicates("pg_name"),
            ]
        )
        return transform(reader.read())


command = ReadProductGroup("data/products.parquet")
data = command()
```
"""
