#!/usr/bin/env python3
"""Check the encoded video against the measured timeline and replay equations."""
import argparse
import hashlib
import json
import math
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import Image

import render as animation


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("media", type=Path, nargs="?", default=Path(__file__).parent / "media")
    folder = parser.parse_args().media.resolve()
    manifest = json.loads((folder / "animation.json").read_text())
    digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    assert digest(Path(animation.__file__)) == manifest["render_source_sha256"]
    assert digest(animation.SOURCE) == manifest["source_sha256"]
    assert digest(animation.FIT_SOURCE) == manifest["fit_sha256"]
    fit = json.loads(animation.FIT_SOURCE.read_text())
    assert fit["fitted_cohorts"] == 120 and fit["source_sha256"] == digest(animation.SOURCE)
    for name, record in manifest["artifacts"].items():
        assert digest(folder / name) == record["sha256"], name
    replay = animation.Replay()
    assert manifest["runtime_axis_log_base"] == 10
    first, last = replay.rows[0], replay.rows[-1]
    assert round(first["seconds"] / last["seconds"]) == 222
    assert round(100 * (1 - last["seconds"] / first["seconds"]), 2) == 99.55
    assert round(100 * (last["rust_seconds"] / last["seconds"] - 1)) == 4
    times = [0, 1, 3.25, 4, 12, 27, 42.6, replay.duration - 1]
    indices = {int(round(t * animation.FPS)) for t in times}
    # Verify the first encoded frame of each of the two new winning cohorts.
    indices.update(math.ceil(t * animation.FPS) for t in replay.transitions[-2:])
    contact_indices = {int(round(t * animation.FPS)) for t in [0, 3.25, 12, 27, 42.6, replay.duration - 1]}
    stream = imageio_ffmpeg.read_frames(str(folder / "mech-rust-optimization-timelapse.mp4"), pix_fmt="rgb24")
    metadata = next(stream)
    assert metadata["fps"] == animation.FPS
    assert metadata["size"] == (animation.WIDTH, animation.HEIGHT)
    records, previews = [], []
    count = 0
    for n, frame in enumerate(stream):
        count += 1
        if n not in indices:
            continue
        pixels = np.frombuffer(frame, np.uint8).reshape(animation.HEIGHT, animation.WIDTH, 3)
        t = n / animation.FPS
        balls = []
        for name, y, phase in [("Mech", 891, replay.phase_at(t)), ("Rust", 978, t / animation.RUST_TRIP_SECONDS)]:
            expected = replay.ball_x(phase)
            left, right = max(0, int(expected) - 18), min(animation.WIDTH, int(expected) + 19)
            patch = pixels[y - 15:y + 16, left:right, :]
            if name == "Mech":
                mask = (patch[:, :, 0] < 75) & (patch[:, :, 1] > 65) & (patch[:, :, 1] < 155) & (patch[:, :, 2] > 145)
            else:
                mask = (patch[:, :, 0] > 150) & (patch[:, :, 1] > 60) & (patch[:, :, 1] < 160) & (patch[:, :, 2] < 110)
            columns = mask.sum(axis=0)
            observed = left + float(np.average(np.arange(len(columns)), weights=columns))
            error = abs(observed - expected)
            assert error < 1.0, (name, t, expected, observed)
            balls.append({"language": name, "expected_x": expected, "decoded_x": observed, "error_px": error})
        row = replay.rows[replay.index_at(t)]
        records.append({"frame": n, "video_seconds": t, "checkpoint": replay.index_at(t) + 1,
                        "measured_x_rust": row["x_rust"], "balls": balls})
        if n in contact_indices:
            previews.append(Image.fromarray(pixels).resize((960, 540), Image.Resampling.LANCZOS))
    assert count == manifest["video_frames"] == replay.frames
    assert len(records) == 10
    assert {r["checkpoint"] for r in records}.issuperset({119, 120})
    report = {"decoded_video": metadata, "decoded_frames": count, "encoded_ball_checks": records,
              "max_ball_error_px": max(b["error_px"] for r in records for b in r["balls"]),
              "retained_individual_observations": replay.verify_motion()["retained_individual_observations"],
              "individual_points_drawn": replay.verify_motion()["individual_points_drawn"],
              "median_points_visible_at_end": replay.verify_motion()["median_points_visible_at_end"],
              "bottom_caption": manifest["bottom_caption"],
              "runtime_axis_log_base": manifest["runtime_axis_log_base"],
              "best_fit_medians": fit["fitted_cohorts"],
              "both_winning_cohorts_checked": True,
              "verifier_sha256": digest(Path(__file__))}
    assert report["median_points_visible_at_end"] == 120 and report["individual_points_drawn"] == 0
    assert not report["bottom_caption"]
    (folder / "encoded-verification.json").write_text(json.dumps(report, indent=2) + "\n")
    sheet = Image.new("RGB", (1920, 1620), "white")
    assert len(previews) == 6
    for i, image in enumerate(previews):
        sheet.paste(image, ((i % 2) * 960, (i // 2) * 540))
    sheet.save(folder / "encoded-contact-sheet.png")
    print(json.dumps({k: v for k, v in report.items() if k not in ["encoded_ball_checks", "decoded_video"]}, indent=2))


if __name__ == "__main__":
    main()
