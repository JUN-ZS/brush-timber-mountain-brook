import unittest
from tail_etf_overlay_v1 import calculate_tail_pnl

class TailOverlayTests(unittest.TestCase):
    def test_tail_rally_offsets_core_loss_after_friction(self):
        raw, friction, net = calculate_tail_pnl(500.0, 10.0, 15.0, 10.0)
        self.assertAlmostEqual(raw, 250.0)
        self.assertAlmostEqual(friction, 0.5)
        self.assertAlmostEqual(net, 249.5)

    def test_tail_decline_can_worsen_core_loss(self):
        raw, friction, net = calculate_tail_pnl(500.0, 10.0, 9.0, 10.0)
        self.assertAlmostEqual(raw, -50.0)
        self.assertAlmostEqual(friction, 0.5)
        self.assertAlmostEqual(net, -50.5)

    def test_zero_friction_has_no_haircut(self):
        raw, friction, net = calculate_tail_pnl(250.0, 10.0, 10.5, 0.0)
        self.assertAlmostEqual(raw, 12.5)
        self.assertAlmostEqual(friction, 0.0)
        self.assertAlmostEqual(net, 12.5)

    def test_invalid_price_rejected(self):
        with self.assertRaises(ValueError):
            calculate_tail_pnl(500.0, 0.0, 10.0, 10.0)

if __name__ == "__main__":
    unittest.main()
