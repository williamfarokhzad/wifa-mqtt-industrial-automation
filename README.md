# MQTT for Industrial Automation: Reject Stale and Duplicate Telemetry

This offline Python project replays synthetic deliveries to a temperature display. It checks when the sensor took a reading, rejects out-of-order sequence numbers, and clears the display after the last reading expires. It never connects to a broker or writes to equipment.

The full tutorial with diagrams and worked examples is at [WIFA Robotics](https://wifarobotics.com/learn/mqtt-industrial-automation/).

## Start from zero

1. Install Python 3.10 or later from [python.org](https://www.python.org/downloads/) and check `python3 --version` (Windows: `py -3 --version`).
2. Use GitHub's **Code → Download ZIP** and extract it. Open a terminal in the folder that contains `replay.py`. No packages or virtual environment are required.
3. Run the commands below. On Windows replace `python3` with `py -3`.

```sh
python3 replay.py examples/retained-then-live.json
python3 replay.py examples/redelivery-and-order.json
python3 replay.py examples/clock-and-topic.json
python3 -m unittest discover -s tests -v
```

The first example shows `expired` at 100 s, `42.0 C` at 101 and 105 s, and `unknown` at 106 s. The second accepts two values and rejects a duplicate, an older sequence and conflicting content. The third accepts a fresh retained reading; it rejects a different topic, a future reading and a sample clock regression. Try `python3 replay.py examples/bad-order.json` for an intentional input error (exit 2).

## Make a trace

Copy an example, keep receiver `at_s` nondecreasing, and use the exact topic `plant/cell-1/motor/temp`. A message has the publisher's `seq`, `sampled_s` and `temp_c` inside `payload`; `retained` and `dup` are observed delivery flags outside the payload. Fixture times are integer seconds on one synthetic timeline. A `tick` asks what the display shows without a delivery. The default fixture threshold is five seconds inclusive.

If the display is unknown, check the difference between `at_s` and the last accepted `sampled_s`. If the clock goes backward, repair the trace's receiver clock rather than sorting by source time: arrival order is part of the exercise. If a device restarts its sequence, this lab will not infer a new stream; real systems need a managed producer epoch or persistent sequence.

## Limits

One trusted producer, one exact topic, one monotonic sequence and comparable clocks. This is a display replay, not an MQTT client, broker test, persistent ingest service or equipment interlock. MQTT 5 delivery semantics are specified by [OASIS](https://docs.oasis-open.org/mqtt/mqtt/v5.0/os/mqtt-v5.0-os.html), not by this trace format. Diagrams are editable SVG with WebP exports.
