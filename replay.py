"""Replay one MQTT application telemetry stream without connecting to a broker."""
import argparse
import json
from pathlib import Path
import sys


TOPIC = "plant/cell-1/motor/temp"


def uint(value, name):
    if type(value) is not int or value < 0:
        raise ValueError(f"{name} must be a nonnegative integer")
    return value


def flag(value, name):
    if type(value) is not bool:
        raise ValueError(f"{name} must be a boolean")
    return value


def temperature(value):
    if type(value) not in (int, float) or not -273.15 <= value <= 1000:
        raise ValueError("temp_c must be a finite number between -273.15 and 1000")
    return float(value)


def replay(trace):
    """Return (receiver seconds, decision, display) for each ordered input row."""
    age_limit = uint(trace["max_age_s"], "max_age_s")
    steps = trace["steps"]
    if not isinstance(steps, list) or not steps:
        raise ValueError("steps must be a nonempty list")
    last = None
    last_rx = -1
    results = []
    for row in steps:
        if not isinstance(row, dict):
            raise ValueError("each step must be a JSON object")
        now = uint(row["at_s"], "at_s")
        if now < last_rx:
            raise ValueError("receiver time must not go backward")
        last_rx = now
        kind = row["kind"]
        if kind == "tick":
            reason = "refresh"
        elif kind == "message":
            flag(row["retained"], "retained")
            flag(row["dup"], "dup")
            if row["topic"] != TOPIC:
                reason = "wrong_topic"
            else:
                payload = row["payload"]
                if not isinstance(payload, dict):
                    raise ValueError("payload must be a JSON object")
                seq = uint(payload["seq"], "seq")
                sampled = uint(payload["sampled_s"], "sampled_s")
                temp = temperature(payload["temp_c"])
                candidate = (seq, sampled, temp)
                if sampled > now:
                    reason = "future_sample"
                elif now - sampled > age_limit:
                    reason = "expired"
                elif last and seq == last[0]:
                    reason = "duplicate" if candidate == last else "sequence_conflict"
                elif last and seq < last[0]:
                    reason = "older_sequence"
                elif last and sampled < last[1]:
                    reason = "sample_clock_regressed"
                else:
                    last = candidate
                    reason = "accepted"
        else:
            raise ValueError("kind must be message or tick")
        display = "unknown" if last is None or now - last[1] > age_limit else f"{last[2]:.1f} C"
        results.append((now, reason, display))
    return results


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path)
    args = parser.parse_args(argv)
    try:
        trace = json.loads(args.trace.read_text(encoding="utf-8"))
        if not isinstance(trace, dict):
            raise ValueError("trace must be a JSON object")
        rows = replay(trace)
    except (OSError, ValueError, KeyError) as error:
        print(f"Invalid trace: {error}", file=sys.stderr)
        return 2
    print(" at_s  decision                 display")
    for now, reason, display in rows:
        print(f"{now:5d}  {reason:23s}  {display}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
