#!/usr/bin/env python3
"""Check the encoded video against the measured timeline and replay equations."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

import imageio_ffmpeg
import numpy as np
from PIL import Image

import render as animation
import bounce_audio


def verify_vectors(folder, replay, manifest, digest):
    assert digest(animation.HERE / "vector_scene.py") == manifest["vector_scene_source_sha256"]
    if "svg_normalization_source_sha256" in manifest:
        assert digest(animation.HERE / "normalize_svg.py") == manifest["svg_normalization_source_sha256"]
    records = []
    for name in ["mech-compiler-optimization.svg", "mech-compiler-optimization-frame.svg"]:
        root = ET.parse(folder / name).getroot()
        images = [e for e in root.iter() if e.tag.endswith("}image")]
        medians = [e for e in root.iter() if e.attrib.get("id", "").startswith("median-")]
        paths = [e for e in root.iter() if e.tag.endswith("}path")]
        assert not images
        assert {e.attrib["id"] for e in medians} == {f"median-{i:03d}" for i in range(120)}
        assert len(paths) > 200
        assert not any(e.tag.endswith("}text") for e in root.iter())  # Fonts are outlined too.
        records.append({"file": name, "embedded_images": 0, "median_markers": len(medians),
                        "vector_paths": len(paths), "fonts": "outlined vector paths",
                        "view_box": root.attrib["viewBox"]})
    # Inspect actual marker-edge coverage in the uncompressed final preview.
    pixels = np.asarray(Image.open(folder / "frame-05.png").convert("RGB"))
    x, y = round(animation.X(0)), round(animation.Y(replay.rows[0]["x_rust"]))
    patch = pixels[y - 7:y + 8, x - 7:x + 8].reshape(-1, 3)
    blue = np.array([23, 109, 202])
    coverage = (255 - patch.astype(float)) / (255 - blue)
    selected = (np.ptp(coverage, axis=1) < .10) & (coverage.mean(axis=1) > .05) & (coverage.mean(axis=1) < .95)
    shades = len(np.unique(patch[selected], axis=0))
    assert shades >= 8, ("Missing marker-edge antialiasing", shades)
    return {"files": records, "antialiased_marker_edge_shades": shades,
            "video_working_pixels": manifest["renderer"]["working_pixels"],
            "downsampling": manifest["renderer"]["downsampling"]}


def verify_audio(folder, replay, manifest, digest):
    report = json.loads((folder / "bounce-audio.json").read_text())
    assert digest(Path(bounce_audio.__file__)) == report["synthesizer_sha256"] == manifest["audio"]["synthesizer_sha256"]
    assert digest(folder / "bounce-soundtrack.flac") == report["soundtrack_sha256"]
    expected = bounce_audio.bounce_events(replay, fps=replay.fps, rust_trip_seconds=animation.RUST_TRIP_SECONDS)
    assert len(expected) == len(report["events"])
    for event, retained in zip(expected, report["events"]):
        assert all(retained[k] == v for k, v in event.items())
        assert abs(retained["sample"] / report["sample_rate"] - event["time_seconds"]) <= .5 / report["sample_rate"]
    duration = replay.frames / replay.fps
    counts = {"Mech": math.floor(replay.phase_at(duration)),
              "Rust": math.ceil(duration / animation.RUST_TRIP_SECONDS) - 1}
    assert report["bounces"] == counts == manifest["audio"]["bounces"]
    decoded = []
    metadata = ""
    for name in ["bounce-soundtrack.flac", "mech-rust-optimization-timelapse.mp4"]:
        result = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-hide_banner", "-v", "info", "-i", str(folder / name),
            "-map", "0:a:0", "-f", "f32le", "-acodec", "pcm_f32le", "-ac", "2", "-ar", "48000", "pipe:1"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        decoded.append(np.frombuffer(result.stdout, "<f4").reshape(-1, 2))
        if name.endswith("mp4"):
            metadata = result.stderr.decode()
            assert "Audio: aac" in metadata and "48000 Hz, stereo" in metadata
    source, encoded = decoded
    assert len(source) == report["samples"] == round(duration * report["sample_rate"])
    assert len(source) <= len(encoded) <= len(source) + 1024
    encoded = encoded[:len(source)]
    correlation = float(np.corrcoef(source.reshape(-1), encoded.reshape(-1))[0, 1])
    peak = float(np.abs(encoded).max())
    rms = float(np.sqrt(np.mean(encoded.astype(np.float64) ** 2)))
    assert correlation > .98, correlation
    assert 0 < peak < .17 and 0 < rms < .025
    return {"codec": "AAC", "sample_rate": report["sample_rate"], "channels": 2,
            "bounces": counts, "all_contacts_checked": True,
            "maximum_event_quantization_seconds": .5 / report["sample_rate"],
            "decoded_peak_dbfs": 20 * math.log10(peak), "decoded_rms_dbfs": 20 * math.log10(rms),
            "zero_lag_correlation_with_lossless_source": correlation, "clipping": False}


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
    fps = manifest["fps"]
    replay = animation.Replay(fps=fps)
    assert manifest["runtime_axis_log_base"] == 10
    first, last = replay.rows[0], replay.rows[-1]
    assert round(first["seconds"] / last["seconds"]) == 222
    assert round(100 * (1 - last["seconds"] / first["seconds"]), 2) == 99.55
    assert round(100 * (last["rust_seconds"] / last["seconds"] - 1)) == 4
    times = [0, 1, 3.25, 4, 12, 27, 42.6, replay.duration - 1]
    indices = {int(round(t * fps)) for t in times}
    if fps == 60:
        # A duplicated 30 fps stream cannot match Rust's position on this intervening frame.
        indices.add(1)
    # Verify the first encoded frame of each of the two new winning cohorts.
    indices.update(math.ceil(t * fps) for t in replay.transitions[-2:])
    ordinary_indices = indices.copy()
    impact_indices = {round((t + dt) * fps) for contacts in replay.contacts.values()
                      for t in contacts for dt in [-1 / 15, 0, 1 / 15, 2 / 15, .2]
                      if 0 <= t + dt < replay.frames / fps}
    indices.update(impact_indices)
    assert not manifest["ball_animation"]["arrows"]
    for name, contacts in replay.contacts.items():
        for crossing, t in enumerate(contacts, 1):
            shape = replay.ball_geometry(name, t)
            assert math.isclose(shape["rx"], animation.BALL_RADIUS * .86, abs_tol=1e-8)
            assert math.isclose(shape["rx"] * shape["ry"], animation.BALL_RADIUS ** 2, abs_tol=1e-8)
            edge = shape["x"] + shape["rx"] if crossing % 2 else shape["x"] - shape["rx"]
            wall = animation.WALL_RIGHT if crossing % 2 else animation.WALL_LEFT
            assert abs(edge - wall) < 1e-8
            settled = replay.ball_geometry(name, t + .22)
            assert math.isclose(settled["rx"], animation.BALL_RADIUS) and settled["y"] == animation.LANES[name]
    contact_indices = {int(round(t * fps)) for t in [0, 3.25, 12, 27, 42.6, replay.duration - 1]}
    stream = imageio_ffmpeg.read_frames(str(folder / "mech-rust-optimization-timelapse.mp4"), pix_fmt="rgb24")
    metadata = next(stream)
    assert metadata["fps"] == fps
    assert metadata["size"] == (animation.WIDTH, animation.HEIGHT)
    records, impact_records, previews = [], [], []
    count = 0
    for n, frame in enumerate(stream):
        count += 1
        if n not in indices:
            continue
        pixels = np.frombuffer(frame, np.uint8).reshape(animation.HEIGHT, animation.WIDTH, 3)
        t = n / fps
        balls = []
        for name in animation.LANES:
            shape = replay.ball_geometry(name, t)
            expected, y = shape["x"], shape["y"]
            left, right = math.floor(expected) - 22, math.floor(expected) + 23
            top = math.floor(y) - 22
            patch = pixels[top:top + 45, left:right, :]
            color = animation.MECH if name == "Mech" else animation.RUST
            target = np.array([int(color[j:j + 2], 16) for j in [1, 3, 5]])
            mask = np.max(np.abs(patch.astype(np.int16) - target), axis=2) < 35
            assert mask.sum() > 350, (name, t, "Ball color missing")
            columns = mask.sum(axis=0)
            observed = left + float(np.average(np.arange(len(columns)), weights=columns))
            error = abs(observed - expected)
            assert error < 1.0, (name, t, expected, observed)
            rows = mask.sum(axis=1)
            observed_y = top + float(np.average(np.arange(len(rows)), weights=rows))
            assert abs(observed_y - y) < 1.0, (name, t, y, observed_y)
            occupied_y, occupied_x = np.nonzero(mask)
            width, height = int(np.ptp(occupied_x)) + 1, int(np.ptp(occupied_y)) + 1
            assert abs(width - 2 * shape["rx"]) < 3 and abs(height - 2 * shape["ry"]) < 3
            # No language-colored arrow or other marker may remain beside the ball.
            lane = pixels[top:top + 45, animation.WALL_LEFT - 2:animation.WALL_RIGHT + 3, :]
            lane_mask = np.max(np.abs(lane.astype(np.int16) - target), axis=2) < 35
            outside_left = max(0, math.floor(expected - shape["rx"] - 3) - animation.WALL_LEFT + 2)
            outside_right = math.ceil(expected + shape["rx"] + 3) - animation.WALL_LEFT + 2
            assert lane_mask[:, :outside_left].sum() == 0 and lane_mask[:, outside_right:].sum() == 0
            balls.append({"language": name, "expected_x": expected, "decoded_x": observed, "error_px": error,
                          "expected_y": y, "decoded_y": observed_y, "decoded_width": width,
                          "decoded_height": height, "expected_rx": shape["rx"], "expected_ry": shape["ry"]})
        row = replay.rows[replay.index_at(t)]
        record = {"frame": n, "video_seconds": t, "checkpoint": replay.index_at(t) + 1,
                  "measured_x_rust": row["x_rust"], "balls": balls}
        if n in ordinary_indices:
            records.append(record)
        if n in impact_indices:
            impact_records.append(record)
        if n in contact_indices:
            previews.append(Image.fromarray(pixels).resize((960, 540), Image.Resampling.LANCZOS))
    assert count == manifest["video_frames"] == replay.frames
    assert len(records) == len(ordinary_indices)
    assert {r["checkpoint"] for r in records}.issuperset({119, 120})
    report = {"decoded_video": metadata, "decoded_frames": count, "encoded_ball_checks": records,
              "fps": fps, "intervening_60fps_frame_checked": fps == 60 and any(r["frame"] == 1 for r in records),
              "max_ball_error_px": max(b["error_px"] for r in records + impact_records for b in r["balls"]),
              "retained_individual_observations": replay.verify_motion()["retained_individual_observations"],
              "individual_points_drawn": replay.verify_motion()["individual_points_drawn"],
              "median_points_visible_at_end": replay.verify_motion()["median_points_visible_at_end"],
              "bottom_caption": manifest["bottom_caption"],
              "runtime_axis_log_base": manifest["runtime_axis_log_base"],
              "best_fit_medians": fit["fitted_cohorts"],
              "both_winning_cohorts_checked": True,
              "ball_colors": manifest["ball_colors"],
              "impact_animation": {"decoded_frames_checked": len(impact_records),
                                   "wall_contacts_checked": sum(map(len, replay.contacts.values())),
                                   "maximum_x_error_px": max(b["error_px"] for r in impact_records for b in r["balls"]),
                                   "maximum_y_error_px": max(abs(b["expected_y"] - b["decoded_y"]) for r in impact_records for b in r["balls"]),
                                   "compressed_width_px": min(b["decoded_width"] for r in impact_records for b in r["balls"]),
                                   "arrows_absent": True, "settled_after_seconds": .22,
                                   "radius_compensated_contacts": True},
              "audio": verify_audio(folder, replay, manifest, digest),
              "vector_artwork": verify_vectors(folder, replay, manifest, digest),
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
