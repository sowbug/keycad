import unittest
from keycad import kle


class TestKle(unittest.TestCase):
    def test_simple(self):
        p = kle.Parser()

        p.handle_dict({})
        self.assertEqual(p.key_count, 0)

        p.handle_dict([["0", "1"], ["2", "3"]])
        self.assertEqual(p.key_count, 4)

    def test_per_key_attributes(self):
        p = kle.Parser()
        p.handle_dict([["A"]])
        self.assertEqual(p.key_count, 1)
        key = p.keys[0]
        self.assertEqual(key.width, 1)

        p = kle.Parser()
        p.handle_dict([[{"w": 2}, "A"]])
        self.assertEqual(p.key_count, 1)
        key = p.keys[0]
        self.assertEqual(key.width, 2)

        p = kle.Parser()
        p.handle_dict([[{"w": 50, "h": 45}, "A"]])
        self.assertEqual(p.key_count, 1)
        key = p.keys[0]
        self.assertEqual(key.width, 50)
        self.assertEqual(key.height, 45)

    def test_sample_files(self):
        SAMPLES = {
            "68keys-io": {
                'key_count': 68,
                'homing_keys': ['F', 'J']
            },
            "ansi-104": {
                'key_count': 104,
                'homing_keys': ['F', 'J']
            },
            "ansi-tkl": {
                'key_count': 87,
                'homing_keys': ['F', 'J']
            },
            "iso-105": {
                'key_count': 105,
                'homing_keys': ['F', 'J']
            },
            "iso-tkl": {
                'key_count': 88,
                'homing_keys': ['F', 'J']
            },
            "number-pad": {
                'key_count': 17
            },
            "planck": {
                'key_count': 47,
                'homing_keys': ['F', 'J']
            },
        }

        p = kle.Parser()
        for basename, s in SAMPLES.items():
            p.load("kle_layouts/%s.json" % (basename))
            self.assertEqual(p.key_count, s['key_count'])
            for key in p.keys:
                self.assertTrue(len(key.labels) > 0)

                if 'homing_keys' in s:
                    if key.labels[0] in s['homing_keys']:
                        self.assertTrue(key.is_homing)


if __name__ == "__main__":
    unittest.main()
