import json
import sys
import tempfile
import unittest
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT / "src"))

from simulator.producer import (  # noqa: E402
    ProducerConfig,
    load_events,
    send_events,
)


class FakeFuture:
    def __init__(self, producer: "FakeProducer") -> None:
        self.producer = producer

    def add_callback(self, callback) -> "FakeFuture":
        callback(self.producer)
        return self

    def add_errback(self, callback) -> "FakeFuture":
        return self


class FakeProducer:
    def __init__(self) -> None:
        self.messages = []
        self.flushed = False
        self.closed = False

    def send(self, topic: str, key: str, value: dict) -> FakeFuture:
        self.messages.append((topic, key, value))
        return FakeFuture(self)

    def flush(self, timeout: float) -> None:
        self.flushed = True

    def close(self, timeout: float) -> None:
        self.closed = True


class ProducerTest(unittest.TestCase):
    def _write_events(self, path: Path, count: int) -> None:
        with path.open("w", encoding="utf-8") as file:
            for index in range(count):
                event = {
                    "event_id": f"event-{index}",
                    "city_id": "city-001",
                    "station_id": f"ST{index % 2 + 1:03d}",
                    "event_time": "2026-01-01 00:00:00",
                    "demand_count": index + 1,
                }
                file.write(json.dumps(event) + "\n")

    def test_load_events_applies_limit(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "events.jsonl"
            self._write_events(path, 5)

            events = list(load_events(path, limit=2))

            self.assertEqual(len(events), 2)
            self.assertEqual(events[0]["event_id"], "event-0")
            self.assertEqual(events[1]["event_id"], "event-1")

    def test_send_events_uses_station_key(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "events.jsonl"
            self._write_events(path, 3)
            fake = FakeProducer()
            config = ProducerConfig(
                input_path=path,
                topic="test-topic",
                rate_per_second=0,
            )

            result = send_events(
                config,
                client_factory=lambda _: fake,
                sleep_fn=lambda _: None,
            )

            self.assertEqual(result.attempted, 3)
            self.assertEqual(result.sent, 3)
            self.assertEqual(result.cycles_completed, 1)
            self.assertEqual(fake.messages[0][0], "test-topic")
            self.assertEqual(fake.messages[0][1], "ST001")
            self.assertTrue(fake.flushed)
            self.assertTrue(fake.closed)

    def test_dry_run_does_not_create_client(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "events.jsonl"
            self._write_events(path, 2)
            config = ProducerConfig(
                input_path=path,
                limit=2,
                dry_run=True,
            )

            result = send_events(
                config,
                client_factory=lambda _: self.fail("client must not be created"),
            )

            self.assertEqual(result.attempted, 2)
            self.assertEqual(result.sent, 0)
            self.assertTrue(result.dry_run)

    def test_dry_run_counts_requested_cycles(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "events.jsonl"
            self._write_events(path, 3)
            config = ProducerConfig(
                input_path=path,
                limit=2,
                cycles=4,
                dry_run=True,
            )

            result = send_events(config)

            self.assertEqual(result.attempted, 8)
            self.assertEqual(result.cycles_completed, 4)

    def test_send_events_can_repeat_cycles(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "events.jsonl"
            self._write_events(path, 3)
            fake = FakeProducer()
            config = ProducerConfig(
                input_path=path,
                limit=1,
                cycles=3,
                rate_per_second=0,
            )

            result = send_events(
                config,
                client_factory=lambda _: fake,
                sleep_fn=lambda _: None,
            )

            self.assertEqual(result.attempted, 3)
            self.assertEqual(result.sent, 3)
            self.assertEqual(result.cycles_completed, 3)
            self.assertFalse(result.interrupted)


if __name__ == "__main__":
    unittest.main()
