"""Tests for kural.engine.streaming_delivery — no mic, GPU, model, or network."""

import time

from kural.engine.streaming_delivery import StreamingDelivery, decide_stream_delivery


class TestDecideStreamDelivery:
    def _call(self, cfg=None, available=True, auto_paste=True, textable=True, rule=None):
        return decide_stream_delivery(cfg, available, auto_paste, textable, rule)

    def test_all_on_returns_true(self):
        assert self._call(cfg={"deliver_to_cursor": True}) is True

    def test_missing_config_key_returns_false(self):
        assert self._call(cfg={}) is False

    def test_none_config_returns_false(self):
        assert self._call(cfg=None) is False

    def test_streaming_unavailable_returns_false(self):
        assert self._call(cfg={"deliver_to_cursor": True}, available=False) is False

    def test_no_auto_paste_returns_false(self):
        assert self._call(cfg={"deliver_to_cursor": True}, auto_paste=False) is False

    def test_not_textable_returns_false(self):
        assert self._call(cfg={"deliver_to_cursor": True}, textable=False) is False

    def test_rule_suppress_returns_false(self):
        assert self._call(cfg={"deliver_to_cursor": True}, rule={"suppress": True}) is False

    def test_rule_auto_paste_false_returns_false(self):
        assert self._call(cfg={"deliver_to_cursor": True}, rule={"auto_paste": False}) is False

    def test_rule_other_key_returns_true(self):
        assert self._call(cfg={"deliver_to_cursor": True}, rule={"something": "else"}) is True


class TestStreamingDelivery:
    def test_start_stop_empty(self):
        delivered = []
        sd = StreamingDelivery(lambda t: delivered.append(t))
        sd.start()
        result = sd.stop()
        assert result == ""
        assert delivered == []

    def test_submit_delivered_in_order(self):
        delivered = []
        sd = StreamingDelivery(lambda t: delivered.append(t))
        sd.start()
        sd.submit_final("hello")
        sd.submit_final("world")
        result = sd.stop()
        assert result == "hello world"
        assert delivered == ["hello ", "world "]

    def test_submitted_any_false_before_submit(self):
        sd = StreamingDelivery(lambda t: None)
        sd.start()
        assert sd.submitted_any is False
        sd.stop()

    def test_submitted_any_true_after_submit(self):
        sd = StreamingDelivery(lambda t: None)
        sd.start()
        sd.submit_final("hi")
        # give worker a moment
        time.sleep(0.05)
        assert sd.submitted_any is True
        sd.stop()

    def test_submit_blank_ignored(self):
        delivered = []
        sd = StreamingDelivery(lambda t: delivered.append(t))
        sd.start()
        sd.submit_final("   ")
        sd.submit_final("")
        result = sd.stop()
        assert result == ""
        assert delivered == []

    def test_had_failure_true_on_deliver_error(self):
        def bad_fn(t):
            raise RuntimeError("boom")

        sd = StreamingDelivery(bad_fn)
        sd.start()
        sd.submit_final("test")
        sd.stop()
        assert sd.had_failure is True

    def test_stop_idempotent(self):
        sd = StreamingDelivery(lambda t: None)
        sd.start()
        sd.submit_final("x")
        result1 = sd.stop()
        result2 = sd.stop()
        assert result1 == result2

    def test_submit_after_stop_ignored(self):
        delivered = []
        sd = StreamingDelivery(lambda t: delivered.append(t))
        sd.start()
        sd.stop()
        sd.submit_final("late")
        assert "late" not in delivered
