import unittest
from keycad import kle


class TestKle(unittest.TestCase):
    def test_simple(self):
        p = kle.Parser()

        p.handle_dict({})
        self.assertEqual(p.key_count, 0)

        p.handle_dict([["0", "1"], ["2", "3"]])
        self.assertEqual(p.key_count, 4)

    def test_sample_files(self):
        SAMPLES = {
            "planck-default": {
                'key_count': 47
            },
            "68keys-io": {
                'key_count': 68
            },
            "number-pad": {
                'key_count': 17
            },
        }

        p = kle.Parser()
        for basename, s in SAMPLES.items():
            p.load("kle_layouts/%s.json" % (basename))
            self.assertEqual(p.key_count, s['key_count'])
            for key in p.keys:
                self.assertTrue(len(key.labels) > 0)


if __name__ == "__main__":
    unittest.main()
