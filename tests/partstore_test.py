import unittest
from keycad import partstore


class TestPartStore(unittest.TestCase):
    def test_instantiation(self):
        store = partstore.PartStore()

        self.assertEqual(len(store.parts), 0)

    def test_basic_usage(self):
        store = partstore.PartStore()

        part = store.get_mcu()
        self.assertEqual(len(store.parts), 1)


if __name__ == "__main__":
    unittest.main()
