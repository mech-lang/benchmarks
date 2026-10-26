"""Audit every encoded frame and impact against receipt-derived timing physics.

This module deliberately does not import the renderer or its motion helpers.
"""
import argparse
import bisect
import hashlib
import json
import math
from pathlib import Path
import subprocess

import imageio_ffmpeg
import numpy as np

HERE = Path(__file__).resolve().parent
FPS, INTRO, RUST_CROSSING = 60, 2.0, 1.2
LEFT, RIGHT, RADIUS = 380, 1815, 14


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("media", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    evidence = json.loads((HERE / "accuracy-audit/receipt-audit.json").read_text())
    source = json.loads((HERE / "timeline.json").read_text())
    assert hashlib.sha256((HERE / "timeline.json").read_bytes()).hexdigest() == evidence["timeline_sha256"]
    rows = evidence["records"]
    end_hour = max((o["timestamp"] - source["t0_timestamp"]) / 3600 for row in source["records"] for o in row["observations"])
    duration = math.ceil((INTRO + end_hour + 5) * 30) / 30
    starts = [0.0] + [INTRO + row["hours"] for row in rows[1:]]
    prefixes = [0.0]
    for i in range(1, len(rows)):
        prefixes.append(prefixes[-1] + (starts[i] - starts[i - 1]) * rows[i - 1]["rust_seconds"] / (RUST_CROSSING * rows[i - 1]["candidate_seconds"]))

    def phase(t):
        i = bisect.bisect_right(starts, t) - 1
        return prefixes[i] + (t - starts[i]) * rows[i]["rust_seconds"] / (RUST_CROSSING * rows[i]["candidate_seconds"])

    def center(value):
        fraction = 1 - abs(value % 2 - 1)
        return LEFT + RADIUS + (RIGHT - LEFT - 2 * RADIUS) * fraction

    events = []
    for number in range(1, math.ceil(duration / RUST_CROSSING)):
        events.append({"language": "Rust", "time_seconds": number * RUST_CROSSING, "crossing": number})
    for number in range(1, math.floor(phase(duration)) + 1):
        i = max(0, bisect.bisect_right(prefixes, number) - 1)
        when = starts[i] + (number - prefixes[i]) * RUST_CROSSING * rows[i]["candidate_seconds"] / rows[i]["rust_seconds"]
        assert when < duration and abs(phase(when) - number) < 1e-10
        events.append({"language": "Mech", "time_seconds": when, "crossing": number})
    events.sort(key=lambda e: (e["time_seconds"], e["language"]))
    retained_audio = json.loads((args.media / "bounce-audio.json").read_text())
    assert len(events) == len(retained_audio["events"]) == 78
    event_error, frame_error = 0.0, 0.0
    for expected, actual in zip(events, retained_audio["events"]):
        assert expected["language"] == actual["language"] and expected["crossing"] == actual["crossing"]
        event_error = max(event_error, abs(expected["time_seconds"] - actual["sample"] / 48000))
        frame_error = max(frame_error, abs(expected["time_seconds"] - round(expected["time_seconds"] * FPS) / FPS))
        assert actual["wall"] == ("right" if expected["crossing"] % 2 else "left")
    assert event_error <= .5 / 48000 + 1e-10 and frame_error <= .5 / FPS + 1e-10

    movie = args.media / "mech-rust-optimization-timelapse.mp4"
    decoder = imageio_ffmpeg.read_frames(str(movie), pix_fmt="rgb24")
    metadata = next(decoder)
    assert metadata["fps"] == FPS and metadata["size"] == (1920, 1080)
    maximum_ball_error, maximum_y_error, maximum_cursor_error = 0.0, 0.0, 0.0
    samples = []
    count = 0
    for n, data in enumerate(decoder):
        count += 1
        t = n / FPS
        pixels = np.frombuffer(data, np.uint8).reshape(1080, 1920, 3)
        hour = min(end_hour, max(0, t - INTRO))
        cursor = 145 + (1815 - 145) * hour / 54
        left = math.floor(cursor) - 5
        patch = pixels[185:691, left:left + 11].astype(np.int16)
        mask = np.max(np.abs(patch - np.array([189, 206, 225])), axis=2) <= 25
        weights = mask.sum(axis=0)
        # The antialiased left spine has a similar color. Once the frontier
        # separates from it, exclude those fixed border columns from detection.
        if cursor > 146.5:
            weights[np.arange(11) + left <= 145] = 0
        assert weights.max() >= 100, (n, "history cursor missing")
        # A cursor spans the plot. Short same-color stair/annotation segments
        # must not pull its measured centroid away from the full-height stripe.
        weights[weights < max(60, .7 * weights.max())] = 0
        observed_cursor = left + float(np.average(np.arange(11), weights=weights))
        maximum_cursor_error = max(maximum_cursor_error, abs(cursor - observed_cursor))
        assert abs(cursor - observed_cursor) < 1.5, (n, cursor, observed_cursor)
        for name, y, value, color in [("Mech", 891, phase(t), [246, 192, 78]),
                                      ("Rust", 978, t / RUST_CROSSING, [139, 74, 45])]:
            expected = center(value)
            x0, y0 = math.floor(expected) - 25, y - 23
            patch = pixels[y0:y0 + 47, x0:x0 + 51].astype(np.int16)
            mask = np.max(np.abs(patch - np.array(color)), axis=2) < 35
            assert mask.sum() > 350, (n, name, "ball missing")
            actual_x = x0 + float(np.average(np.arange(51), weights=mask.sum(axis=0)))
            actual_y = y0 + float(np.average(np.arange(47), weights=mask.sum(axis=1)))
            error = abs(actual_x - expected)
            maximum_ball_error = max(maximum_ball_error, error)
            maximum_y_error = max(maximum_y_error, abs(actual_y - y))
            # Impact radius compensation shifts the surface center by at most
            # 1.96 px; lift is at most 2 px. Timing remains the integrated phase.
            assert error < 3.5 and abs(actual_y - y) < 3.5, (n, name, expected, actual_x, y, actual_y)
        if n in [0, 120, 195, 720, 1620, 2556, 3360, 3425]:
            samples.append({"frame": n, "video_seconds": t, "elapsed_hours": hour,
                            "checkpoint": bisect.bisect_right([r["hours"] for r in rows], hour),
                            "expected_clock_text": f"{int(hour * 60) // 60:02d} h {int(hour * 60) % 60:02d} m",
                            "clock_holding": t < INTRO or t >= INTRO + end_hour})
    assert count == round(duration * FPS) == 3426

    decoded = []
    for name in ["bounce-soundtrack.flac", "mech-rust-optimization-timelapse.mp4"]:
        raw = subprocess.check_output([imageio_ffmpeg.get_ffmpeg_exe(), "-v", "error", "-i", str(args.media / name),
            "-map", "0:a:0", "-f", "f32le", "-ac", "2", "-ar", "48000", "pipe:1"])
        decoded.append(np.frombuffer(raw, "<f4").reshape(-1, 2))
    master, encoded = decoded
    assert len(master) == round(duration * 48000) and len(encoded) >= len(master)
    encoded = encoded[:len(master)]
    correlations, lags = [], []
    for event in events:
        start = max(0, round((event["time_seconds"] - .02) * 48000))
        end = min(len(master), round((event["time_seconds"] + .14) * 48000))
        a = master[start:end:4].mean(axis=1).astype(np.float64)
        b = encoded[start:end:4].mean(axis=1).astype(np.float64)
        correlation = float(a.dot(b) / math.sqrt(a.dot(a) * b.dot(b)))
        assert correlation > .98
        correlations.append(correlation)
        size = 1 << (2 * len(a) - 1).bit_length()
        cross = np.fft.irfft(np.fft.rfft(b, size) * np.conj(np.fft.rfft(a, size)), size)
        maximum_lag = 240  # +/-20 ms at the downsampled 12 kHz audit rate.
        local = np.concatenate([cross[-maximum_lag:], cross[:maximum_lag + 1]])
        lag = (int(local.argmax()) - maximum_lag) * 4 / 48000
        assert abs(lag) <= 4 / 48000
        lags.append(lag)
    report = {"status": "passed", "encoded_frames_checked": count, "fps": FPS,
              "video_duration_seconds": duration, "history_hours": end_hour,
              "history_seconds_per_hour": 1.0, "intro_hold_seconds": INTRO,
              "encoded_outro_hold_seconds": duration - INTRO - end_hour,
              "rust_crossing_seconds": RUST_CROSSING,
              "maximum_history_cursor_error_px": maximum_cursor_error,
              "maximum_ball_center_error_including_deformation_px": maximum_ball_error,
              "maximum_vertical_lift_including_pixel_error_px": maximum_y_error,
              "sound_contacts_checked": len(events), "maximum_audio_event_quantization_seconds": event_error,
              "maximum_contact_to_nearest_frame_seconds": frame_error,
              "minimum_per_contact_aac_master_correlation": min(correlations),
              "maximum_per_contact_audio_lag_seconds": max(map(abs, lags)),
              "clock_checkpoints": samples,
              "video_sha256": hashlib.sha256(movie.read_bytes()).hexdigest(),
              "receipt_audit_sha256": hashlib.sha256((HERE / "accuracy-audit/receipt-audit.json").read_bytes()).hexdigest(),
              "auditor_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "method": "Independent receipt-derived piecewise integration; decode every frame and compare measured pixels, history frontier and per-impact audio alignment. No renderer imports."}
    (args.output / "playback-audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "clock_checkpoints"}, indent=2))


if __name__ == "__main__":
    main()
