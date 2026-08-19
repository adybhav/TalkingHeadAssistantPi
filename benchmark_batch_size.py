"""
Benchmark MuseTalk inference speed across different --batch_size values.

batch_size is fixed at MuseTalk subprocess startup (it's a CLI arg), so we
spin up a fresh worker per batch size, time the same audio clip against it,
then close it before moving to the next size.

Usage:
    py .\\benchmark_batch_size.py
"""
from __future__ import annotations

import statistics
import time
from pathlib import Path

from modules.tts import text_to_speech
from musetalk_runner import MuseTalkWorker

BATCH_SIZES = [5]  # , 10, 12, 14, 16]
WARMUP_RUNS = 1  # excluded from timing; each run is ~230s so keep this low
TIMED_RUNS = 2

BENCHMARK_TEXT = (
    "This is a benchmark test lol"
)

AUDIO_PATH = Path("benchmark_audio.wav")
OUTPUT_DIR = Path("benchmark_output")


def main() -> None:
    if not AUDIO_PATH.is_file():
        print(f"Generating benchmark audio with TTS -> {AUDIO_PATH}")
        text_to_speech(BENCHMARK_TEXT, str(AUDIO_PATH))

    OUTPUT_DIR.mkdir(exist_ok=True)

    total_runs = WARMUP_RUNS + TIMED_RUNS
    print(
        f"{len(BATCH_SIZES)} batch size(s), "
        f"{WARMUP_RUNS} warm-up + {TIMED_RUNS} timed run(s) each "
        f"({total_runs} runs per batch size)."
    )

    results: dict[int, list[float]] = {}

    for batch_size in BATCH_SIZES:
        print(f"\n=== batch_size={batch_size} ===")
        worker = MuseTalkWorker(batch_size=batch_size)
        timings: list[float] = []

        try:
            for run_index in range(total_runs):
                output_path = OUTPUT_DIR / f"bs{batch_size}_run{run_index}.mp4"
                is_warmup = run_index < WARMUP_RUNS

                start = time.perf_counter()
                worker.generate(AUDIO_PATH, output_path)
                elapsed = time.perf_counter() - start

                label = "warm-up" if is_warmup else "timed"
                print(f"  run {run_index} ({label}): {elapsed:.2f}s")

                if not is_warmup:
                    timings.append(elapsed)
        finally:
            worker.close()

        results[batch_size] = timings

        if timings:
            print(
                f"  -> avg={statistics.mean(timings):.2f}s min={min(timings):.2f}s"
            )

    print("\n=== Results (warm-up run excluded) ===")
    for batch_size, timings in results.items():
        if timings:
            formatted = [f"{t:.2f}" for t in timings]
            print(
                f"batch_size={batch_size:>2}: "
                f"avg={statistics.mean(timings):.2f}s "
                f"min={min(timings):.2f}s "
                f"runs={formatted}"
            )
        else:
            print(f"batch_size={batch_size:>2}: no timed runs")

    timed_batch_sizes = [bs for bs, t in results.items() if t]
    if timed_batch_sizes:
        fastest = min(timed_batch_sizes, key=lambda bs: statistics.mean(results[bs]))
        print(f"\nFastest batch_size: {fastest}")


if __name__ == "__main__":
    main()
