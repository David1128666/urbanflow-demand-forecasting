from __future__ import annotations

import argparse
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable

from simulator import __version__


REQUIRED_FIELDS = {
    "event_id",
    "city_id",
    "station_id",
    "event_time",
    "demand_count",
}


@dataclass(frozen=True)
class ProducerConfig:
    """Configuration for sending generated events to Kafka."""

    input_path: Path
    bootstrap_servers: str = "node1:9092"
    topic: str = "urbanflow-demand-events"
    limit: int = 0
    cycles: int = 1
    rate_per_second: float = 100.0
    timeout_seconds: float = 30.0
    dry_run: bool = False

    def validate(self) -> None:
        if not self.input_path.is_file():
            raise FileNotFoundError(f"input file not found: {self.input_path}")
        if not self.bootstrap_servers:
            raise ValueError("bootstrap_servers cannot be empty")
        if not self.topic:
            raise ValueError("topic cannot be empty")
        if self.limit < 0:
            raise ValueError("limit cannot be negative")
        if self.cycles < 0:
            raise ValueError("cycles cannot be negative")
        if self.rate_per_second < 0:
            raise ValueError("rate_per_second cannot be negative")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")


@dataclass(frozen=True)
class ProducerResult:
    attempted: int
    sent: int
    dry_run: bool
    cycles_completed: int
    interrupted: bool


def load_events(
    input_path: Path,
    limit: int = 0,
) -> Iterable[dict[str, Any]]:
    """Load and validate demand events from a JSONL file."""

    count = 0
    with Path(input_path).open(encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            stripped = line.strip()
            if not stripped:
                continue

            try:
                event = json.loads(stripped)
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"invalid JSON at line {line_number}: {error}"
                ) from error

            yield _validate_event(event, line_number)
            count += 1
            if limit and count >= limit:
                return


def send_events(
    config: ProducerConfig,
    *,
    client_factory: Callable[[ProducerConfig], Any] | None = None,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> ProducerResult:
    """Send generated demand events to Kafka."""

    config.validate()
    if config.dry_run:
        if config.cycles == 0:
            raise ValueError("dry_run does not support infinite cycles")
        per_cycle = sum(1 for _ in load_events(config.input_path, config.limit))
        attempted = per_cycle * config.cycles
        return ProducerResult(
            attempted=attempted,
            sent=0,
            dry_run=True,
            cycles_completed=config.cycles,
            interrupted=False,
        )

    factory = client_factory or _create_kafka_producer
    producer = factory(config)
    attempted = 0
    sent = 0
    cycles_completed = 0
    interrupted = False
    errors: list[str] = []

    def on_success(_: Any) -> None:
        nonlocal sent
        sent += 1

    def on_error(error: BaseException) -> None:
        errors.append(str(error))

    try:
        while config.cycles == 0 or cycles_completed < config.cycles:
            cycles_completed += 1
            if config.cycles == 0 or config.cycles > 1:
                print(f"Starting producer cycle {cycles_completed}")

            for event in load_events(config.input_path, config.limit):
                attempted += 1
                future = producer.send(
                    config.topic,
                    key=str(event["station_id"]),
                    value=event,
                )
                future.add_callback(on_success)
                future.add_errback(on_error)

                if config.rate_per_second > 0:
                    sleep_fn(1.0 / config.rate_per_second)

                if attempted % 1000 == 0:
                    print(f"Sent {attempted} events")

        producer.flush(timeout=config.timeout_seconds)
    except KeyboardInterrupt:
        interrupted = True
        print("Stop signal received; flushing Kafka producer...")
    finally:
        producer.close(timeout=config.timeout_seconds)

    if errors:
        raise RuntimeError(
            f"{len(errors)} events failed; first error: {errors[0]}"
        )

    return ProducerResult(
        attempted=attempted,
        sent=sent,
        dry_run=False,
        cycles_completed=cycles_completed,
        interrupted=interrupted,
    )


def _validate_event(
    event: Any,
    line_number: int,
) -> dict[str, Any]:
    if not isinstance(event, dict):
        raise ValueError(f"event at line {line_number} must be a JSON object")

    missing = sorted(REQUIRED_FIELDS - event.keys())
    if missing:
        raise ValueError(
            f"event at line {line_number} is missing fields: {missing}"
        )

    demand_count = event["demand_count"]
    if isinstance(demand_count, bool) or not isinstance(demand_count, int):
        raise ValueError(
            f"event at line {line_number} has non-integer demand_count"
        )
    if demand_count < 0:
        raise ValueError(
            f"event at line {line_number} has negative demand_count"
        )

    for field in ("event_id", "city_id", "station_id", "event_time"):
        if not isinstance(event[field], str) or not event[field]:
            raise ValueError(
                f"event at line {line_number} has invalid {field}"
            )

    return event


def _create_kafka_producer(config: ProducerConfig) -> Any:
    try:
        from kafka import KafkaProducer
    except ImportError as error:
        raise RuntimeError(
            "kafka-python is required; install the simulator package first"
        ) from error

    return KafkaProducer(
        bootstrap_servers=config.bootstrap_servers.split(","),
        acks="all",
        retries=5,
        linger_ms=50,
        enable_idempotence=True,
        key_serializer=lambda key: key.encode("utf-8"),
        value_serializer=lambda value: json.dumps(
            value,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8"),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Send UrbanFlow virtual demand events to Kafka."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/virtual-v1/demand_observations.jsonl"),
        help="Demand event JSONL file",
    )
    parser.add_argument(
        "--bootstrap-servers",
        default=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "node1:9092"),
        help="Kafka broker address",
    )
    parser.add_argument(
        "--topic",
        default=os.getenv("KAFKA_DEMAND_TOPIC", "urbanflow-demand-events"),
        help="Kafka Topic",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Maximum events to send; 0 means all",
    )
    parser.add_argument(
        "--cycles",
        type=int,
        default=1,
        help="Number of cycles; 0 means continuous",
    )
    parser.add_argument(
        "--rate",
        type=float,
        default=100.0,
        help="Events per second; 0 means unlimited",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="Timeout in seconds for producer flush and close",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate events without connecting to Kafka",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    config = ProducerConfig(
        input_path=args.input,
        bootstrap_servers=args.bootstrap_servers,
        topic=args.topic,
        limit=args.limit,
        cycles=args.cycles,
        rate_per_second=args.rate,
        timeout_seconds=args.timeout,
        dry_run=args.dry_run,
    )
    result = send_events(config)

    print(f"UrbanFlow producer {__version__}")
    print(f"Kafka：{config.bootstrap_servers}")
    print(f"Topic：{config.topic}")
    print(f"Events processed: {result.attempted}")
    print(f"Events sent: {result.sent}")
    print(f"Cycles completed: {result.cycles_completed}")
    print(f"Interrupted: {result.interrupted}")
    print(f"Dry run：{result.dry_run}")


if __name__ == "__main__":
    main()
