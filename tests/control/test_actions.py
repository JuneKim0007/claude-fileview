import os
import signal
import unittest

from fileview.control import signals
from fileview.control.actions import ActionRegistry


class Registry(unittest.TestCase):
    def test_requested_actions_run_once_in_order(self):
        registry, ran = ActionRegistry(), []
        registry.register("reload", lambda target: ran.append(("reload", target)))
        registry.register("redraw", lambda target: ran.append(("redraw", target)))
        for name in ("reload", "redraw", "reload", "unknown"):
            registry.request(name)
        self.assertEqual(registry.run_pending("viewer"), ["reload", "redraw"])
        self.assertEqual(ran, [("reload", "viewer"), ("redraw", "viewer")])
        self.assertEqual(registry.run_pending("viewer"), [])


class Signals(unittest.TestCase):
    def test_a_signal_only_queues_its_action(self):
        previous = {s: signal.getsignal(s) for s in signals.SIGNAL_FOR_ACTION.values()}
        self.addCleanup(lambda: [signal.signal(s, h) for s, h in previous.items()])
        registry, ran = ActionRegistry(), []
        registry.register("reload", lambda _target: ran.append("reload"))
        signals.install(registry)
        os.kill(os.getpid(), signal.SIGHUP)
        self.assertEqual(ran, [])                                     # nothing runs inside the handler
        self.assertEqual(registry.run_pending(None), ["reload"])


if __name__ == "__main__":
    unittest.main()
