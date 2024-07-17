"""This package holds all the transformations that can be applied to the data.

Use eliza-data when possible and extend/override when it does not suit your needs. For example:

```python
from eliza.data.transforms import DataTransform


class DropBadDescriptions(DataTransform):
    def __init__(self, description: str, nan_key: str, **kwargs):
        super().__init__(**kwargs)
        self.description = description
        self.nan_key = nan_key

    @override
    def _transform(self, dataset: Dataset) -> PandasDataset:
        data = dataset.pandas
        bad_desc = data.groupby(self.description).count().reset_index()
        bad_desc = bad_desc[bad_desc[self.nan_key] > 1][self.description].unique()
        data = data[~(data[self.description].isin(bad_desc))]
        return PandasDataset(data)
```
"""
