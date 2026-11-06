import contextlib
import io
import json
import pathlib
import unittest

from replay import TOPIC, main, replay


def load(name):
    return json.loads((pathlib.Path(__file__).resolve().parents[1] / "examples" / f"{name}.json").read_text())


def msg(now, sample, seq=1, **extra):
    return {"at_s": now, "kind": "message", "topic": TOPIC, "retained": False,
            "dup": False, "payload": {"seq": seq, "sampled_s": sample, "temp_c": 23},
            **extra}


class ReplayTests(unittest.TestCase):
    def test_retained_then_live_boundary_and_silence(self):
        self.assertEqual(replay(load("retained-then-live")), [
            (100, "expired", "unknown"), (101, "accepted", "42.0 C"),
            (105, "refresh", "42.0 C"), (106, "refresh", "unknown")])

    def test_equal_sequences_and_late_message_do_not_change_display(self):
        self.assertEqual(replay(load("redelivery-and-order")), [
            (101, "accepted", "42.0 C"), (102, "duplicate", "42.0 C"),
            (103, "older_sequence", "42.0 C"), (104, "sequence_conflict", "42.0 C"),
            (105, "accepted", "43.0 C")])

    def test_wrong_topic_future_and_clock_regression(self):
        self.assertEqual(replay(load("clock-and-topic")), [
            (101, "wrong_topic", "unknown"), (102, "future_sample", "unknown"),
            (103, "accepted", "43.0 C"), (104, "sample_clock_regressed", "43.0 C"),
            (108, "refresh", "unknown")])

    def test_rejected_high_sequence_does_not_advance_watermark(self):
        self.assertEqual(replay({"max_age_s": 3, "steps": [msg(5, 6, 99), msg(6, 5, 3)]}),
                         [(5, "future_sample", "unknown"), (6, "accepted", "23.0 C")])

    def test_expired_value_is_rejected_with_or_without_retain_flag(self):
        for retained in (False, True):
            with self.subTest(retained=retained):
                self.assertEqual(replay({"max_age_s": 0, "steps": [msg(4, 3, retained=retained)]}),
                                 [(4, "expired", "unknown")])

    def test_timestamp_type_rejects_boolean(self):
        with self.assertRaisesRegex(ValueError, "sampled_s"):
            replay({"max_age_s": 5, "steps": [msg(2, True)]})

    def test_nonfinite_temperature_is_rejected(self):
        for temp in (float("nan"), float("inf"), -float("inf")):
            with self.subTest(temp=temp), self.assertRaisesRegex(ValueError, "temp_c"):
                replay({"max_age_s": 5, "steps": [
                    msg(2, 1, payload={"seq": 1, "sampled_s": 1, "temp_c": temp})]})

    def test_bad_order_cli_returns_two_and_prints_no_partial_results(self):
        with contextlib.redirect_stderr(io.StringIO()) as err, contextlib.redirect_stdout(io.StringIO()) as out:
            code = main([str(pathlib.Path(__file__).resolve().parents[1] / "examples/bad-order.json")])
        self.assertEqual(code, 2)
        self.assertEqual(out.getvalue(), "")
        self.assertIn("receiver time must not go backward", err.getvalue())


if __name__ == "__main__":
    unittest.main()
