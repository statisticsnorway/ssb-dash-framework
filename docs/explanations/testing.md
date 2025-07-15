### Tests for your module

Your module needs to have a unit test making sure the top level import works as intended. In order to keep the code flexible and reduce the amount of breaking changes, we strongly encourage users to import from the top level. Because of this we need a unit test to ensure this functionality remains intact.

```python
from ssb_dash_framework import MyModule
```

Therefore, your test should look something like this:

```python
def test_import():
    from ssb_dash_framework import MyModule
    assert MyModule is not None
```
