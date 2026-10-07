import unittest

from fileview.control.debounce import Debounce


class Debouncing(unittest.TestCase):
    def test_a_burst_fires_once_after_it_goes_quiet(self):
        debounce = Debounce(quiet=0.5)
        for t in (0.0, 0.1, 0.2, 0.3):          # a window drag
            debounce.poke(now=t)
            self.assertFalse(debounce.due(now=t + 0.05))
        self.assertFalse(debounce.due(now=0.7))
        self.assertTrue(debounce.due(now=0.81))
        self.assertFalse(debounce.due(now=2.0))  # once only

    def test_nothing_due_without_a_poke(self):
        self.assertFalse(Debounce(quiet=0.5).due(now=100))


if __name__ == "__main__":
    unittest.main()
