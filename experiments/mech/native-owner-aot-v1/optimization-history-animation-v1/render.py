#!/usr/bin/env python3
"""Animate the retained history and replay measured, piecewise-constant speeds."""
from __future__ import annotations

import argparse
import bisect
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import subprocess
import sys

os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/mech-history-animation-matplotlib")
os.environ.setdefault("XDG_CACHE_HOME", "/private/tmp/mech-history-animation-cache")
import imageio_ffmpeg
import matplotlib
matplotlib.use("Agg")
from matplotlib import pyplot as plt
from matplotlib.ticker import FixedLocator, FuncFormatter
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from bounce_audio import bounce_events, create_soundtrack

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = HERE / "timeline.json"
FIT_SOURCE = HERE / "best-fit.json"
WIDTH, HEIGHT = 1920, 1080
PLOT = (145, 185, 1815, 690)
FPS = 30
INTRO_SECONDS = 2.0
OUTRO_SECONDS = 5.0
HISTORY_SPEEDUP = 3600.0  # One elapsed optimization hour per video second.
RUST_TRIP_SECONDS = 1.2  # Separate illustrative clock, identical in both lanes.
TITLE_LINES = (
    "LLM Optimizes Mech Compiler 222× Over 50 Hours",
    "99.55% Runtime Reduction · 4% Faster Than Rust Baseline",
)
BLUE = "#176DCA"
MECH = "#F6C04E"  # Mech logo: rgb(246 192 78).
INK = "#1B2B3B"
MUTED = "#53677E"
RUST = "#8B4A2D"
BALL_RADIUS = 14.0
WALL_LEFT, WALL_RIGHT = 380, 1815
LANES = {"Mech": 891, "Rust": 978}
FONT = Path(matplotlib.get_data_path()) / "fonts/ttf/DejaVuSans.ttf"
BOLD = FONT.with_name("DejaVuSans-Bold.ttf")
FONTS: dict[tuple[int, bool], ImageFont.FreeTypeFont] = {}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    key = (size, bold)
    if key not in FONTS:
        FONTS[key] = ImageFont.truetype(str(BOLD if bold else FONT), size)
    return FONTS[key]


def text(draw, xy, value, size=20, color=INK, bold=False, anchor="la"):
    draw.text(xy, value, font=font(size, bold), fill=color, anchor=anchor)


def ratio_label(value: float) -> str:
    digits = 0 if value >= 100 else 1 if value >= 10 else 2 if value >= 1 else 3
    return f"{value:.{digits}f}×"


def seconds_label(value: float) -> str:
    digits = 1 if value >= 100 else 2 if value >= 1 else 3
    return f"{value:.{digits}f} s"


def X(hours: float) -> float:
    return PLOT[0] + (PLOT[2] - PLOT[0]) * hours / 54.0


def Y(ratio: float) -> float:
    return PLOT[3] - (PLOT[3] - PLOT[1]) * math.log(ratio / 0.5) / math.log(640)


def make_base() -> Image.Image:
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 14,
                         "text.color": INK, "axes.labelcolor": INK,
                         "xtick.color": MUTED, "ytick.color": MUTED})
    fig = plt.figure(figsize=(WIDTH / 100, HEIGHT / 100), dpi=100, facecolor="white")
    left, top, right, bottom = PLOT
    ax = fig.add_axes([left / WIDTH, (HEIGHT - bottom) / HEIGHT,
                       (right - left) / WIDTH, (bottom - top) / HEIGHT])
    ax.set_xlim(0, 54)
    ax.set_ylim(0.5, 320)
    ax.set_yscale("log", base=10)
    ax.xaxis.set_major_locator(FixedLocator(range(0, 55, 6)))
    ax.yaxis.set_major_locator(FixedLocator([0.5, 1, 2, 5, 10, 20, 50, 100, 200]))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda y, _: f"{y:g}×"))
    ax.minorticks_off()
    ax.grid(color="#E4ECF4", linewidth=0.9)
    ax.axhline(1, color="#ACBED0", linestyle=(0, (5, 4)), linewidth=1.2)
    ax.set_xlabel("Elapsed optimization time (hours)", labelpad=15, fontsize=16)
    ax.set_ylabel("Mech / Rust runtime · log₁₀", labelpad=22, fontsize=16)
    for edge in ["top", "right"]:
        ax.spines[edge].set_visible(False)
    for edge in ["left", "bottom"]:
        ax.spines[edge].set_color("#94A6BA")
    ax.tick_params(length=0, pad=11)
    fig.canvas.draw()
    image = Image.fromarray(np.asarray(fig.canvas.buffer_rgba())[:, :, :3].copy())
    plt.close(fig)
    d = ImageDraw.Draw(image)
    text(d, (55, 16), TITLE_LINES[0], 38, bold=True)
    text(d, (55, 64), TITLE_LINES[1], 33, bold=True)
    text(d, (57, 111), "K-nucleotide · 125 million bases · complete process, including startup", 20, MUTED)
    text(d, (1455, 28), "OPTIMIZATION CLOCK  ·  3,600×", 17, MUTED, bold=True)
    # Legend uses the same colors as the original white-background chart.
    d.ellipse((58, 154, 70, 166), fill=BLUE)
    text(d, (83, 145), "Measured medians", 19)
    for x in range(510, 560, 16):
        d.line((x, 160, x + 9, 160), fill="#7E8D9E", width=2)
    text(d, (572, 145), "Line of best fit", 19)
    text(d, (1815, 145), "Lower is faster", 19, MUTED, anchor="ra")
    text(d, (1802, Y(1) - 29), "Rust = 1×", 18, MUTED, anchor="ra")
    # The replay lanes are separate from the elapsed-hour chart.
    d.rounded_rectangle((55, 791, 1865, 1033), radius=22, fill="#F5F8FC", outline="#E0E8F2", width=1)
    text(d, (83, 805), "BENCHMARK SPEED REPLAY", 16, MUTED, bold=True)
    for name, y, color in [("Mech", 891, MECH), ("Rust", 978, RUST)]:
        d.ellipse((85, y - 28, 101, y - 12), fill=color)
        text(d, (111, y - 39), name, 29, INK, bold=True)
        d.line((380, y, 1815, y), fill="#CCD8E5", width=3)
        d.line((380, y - 19, 380, y + 19), fill="#A3B3C5", width=3)
        d.line((1815, y - 19, 1815, y + 19), fill="#A3B3C5", width=3)
    text(d, (85, 978), "1.00× reference", 20, MUTED)
    return image


class Replay:
    def __init__(self):
        self.data = json.loads(SOURCE.read_text())
        self.fit = json.loads(FIT_SOURCE.read_text())["drawn_fit"]
        self.rows = sorted(self.data["records"], key=lambda r: r["hours"])
        self.hours = [r["hours"] for r in self.rows]
        assert len(self.rows) == self.data["cohorts"] == 120
        assert sum(r["n"] for r in self.rows) == self.data["process_observations"] == 732
        assert all(a < b for a, b in zip(self.hours, self.hours[1:]))
        for r in self.rows:
            assert math.isclose(r["seconds"] / r["rust_seconds"], r["x_rust"], rel_tol=1e-12)
        self.end_hour = self.hours[-1]
        self.history_seconds = self.end_hour * 3600 / HISTORY_SPEEDUP
        self.duration = INTRO_SECONDS + self.history_seconds + OUTRO_SECONDS
        self.frames = math.ceil(self.duration * FPS)
        # Each speed is held, including regressions; no fitted or interpolated speed.
        self.transitions = [0.0] + [INTRO_SECONDS + h * 3600 / HISTORY_SPEEDUP for h in self.hours[1:]]
        self.phases = [0.0]
        for i in range(1, len(self.rows)):
            dt = self.transitions[i] - self.transitions[i - 1]
            self.phases.append(self.phases[-1] + dt / self.trip_seconds(i - 1))
        self.samples = []
        for r in self.rows:
            for o in r["observations"]:
                h = (o["timestamp"] - self.data["t0_timestamp"]) / 3600
                self.samples.append((h, o["seconds"] / r["rust_seconds"]))
        self.samples.sort()
        assert len(self.samples) == 732
        # A cohort is positioned at its median process launch. Its later individual
        # observations must still be revealed before the ending hold begins.
        self.end_hour = max(self.end_hour, self.samples[-1][0])
        self.history_seconds = self.end_hour * 3600 / HISTORY_SPEEDUP
        self.duration = INTRO_SECONDS + self.history_seconds + OUTRO_SECONDS
        self.frames = math.ceil(self.duration * FPS)
        contacts = bounce_events(self, fps=FPS, rust_trip_seconds=RUST_TRIP_SECONDS)
        self.contacts = {name: [e["time_seconds"] for e in contacts if e["language"] == name]
                         for name in LANES}
        self.base = make_base()
        self.curve_layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        curve = ImageDraw.Draw(self.curve_layer)
        points = []
        for i in range(1601):
            h = self.hours[-1] * i / 1600
            p = self.fit
            value = p["C"] + p["A_fast"] * math.exp(-p["k_fast"] * h) + p["A_slow"] * math.exp(-p["k_slow"] * h)
            points.append((X(h), Y(value)))
        distance = 0.0
        for a, b in zip(points, points[1:]):
            length = math.dist(a, b)
            if int(distance / 10) % 2 == 0:
                curve.line([a, b], fill=(116, 131, 149, 180), width=2)
            distance += length

    def trip_seconds(self, i: int) -> float:
        return RUST_TRIP_SECONDS * self.rows[i]["x_rust"]

    def index_at(self, t: float) -> int:
        return max(0, bisect.bisect_right(self.transitions, t) - 1)

    def phase_at(self, t: float) -> float:
        i = self.index_at(t)
        return self.phases[i] + (t - self.transitions[i]) / self.trip_seconds(i)

    @staticmethod
    def ball_x(phase: float) -> float:
        p = phase % 2
        fraction = p if p <= 1 else 2 - p
        return WALL_LEFT + BALL_RADIUS + (WALL_RIGHT - WALL_LEFT - 2 * BALL_RADIUS) * fraction

    def ball_geometry(self, name: str, t: float) -> dict:
        phase = self.phase_at(t) if name == "Mech" else t / RUST_TRIP_SECONDS
        fraction = 1 - abs(phase % 2 - 1)
        contacts = self.contacts[name]
        index = bisect.bisect_left(contacts, t)
        neighbors = contacts[max(0, index - 1):index + 1]
        contact = min(neighbors, key=lambda value: abs(value - t))
        dt = t - contact
        smooth = lambda x: x * x * (3 - 2 * x)
        deformation = 0.0
        if -.065 < dt <= 0:
            deformation = -.14 * smooth((dt + .065) / .065)
        elif 0 < dt < .065:
            deformation = -.14 * (1 - smooth(dt / .065))
        elif .065 <= dt < .185:
            deformation = .04 * math.sin(math.pi * (dt - .065) / .12) ** 2
        rx = BALL_RADIUS * (1 + deformation)
        ry = BALL_RADIUS / (1 + deformation)
        lift = 2 * math.sin(math.pi * dt / .21) ** 2 if 0 < dt < .21 else 0.0
        # Radius compensation keeps the deformed edge on the wall at contact.
        # The measured phase and its collision times remain unchanged.
        x = WALL_LEFT + rx + (WALL_RIGHT - WALL_LEFT - 2 * rx) * fraction
        return {"x": x, "y": LANES[name] - lift, "rx": rx, "ry": ry,
                "contact_seconds": contact, "contact_offset_seconds": dt,
                "measured_center_x": self.ball_x(phase)}

    def draw_ball(self, image: Image.Image, name: str, t: float):
        shape = self.ball_geometry(name, t)
        x, y, rx, ry = (shape[k] for k in ["x", "y", "rx", "ry"])
        left, top = math.floor(x) - 24, math.floor(y) - 24
        scale = 4
        sprite = Image.new("RGBA", (48 * scale, 48 * scale))
        draw = ImageDraw.Draw(sprite)
        bounds = [(x - rx - left) * scale, (y - ry - top) * scale,
                  (x + rx - left) * scale, (y + ry - top) * scale]
        draw.ellipse(bounds, fill=MECH if name == "Mech" else RUST)
        # The highlight deforms with the surface instead of floating above it.
        draw.ellipse(((x - 5 * rx / BALL_RADIUS - left) * scale,
                      (y - 8 * ry / BALL_RADIUS - top) * scale,
                      (x + rx / BALL_RADIUS - left) * scale,
                      (y - 2 * ry / BALL_RADIUS - top) * scale), fill="white")
        sprite = sprite.resize((48, 48), Image.Resampling.LANCZOS)
        image.paste(sprite, (left, top), sprite)

    def frame(self, t: float) -> Image.Image:
        h = max(0.0, min(self.end_hour, (t - INTRO_SECONDS) * HISTORY_SPEEDUP / 3600))
        i = self.index_at(t)
        row = self.rows[i]
        image = self.base.copy()
        # Reveal the descriptive fit only as the same elapsed-hour frontier passes.
        if h > 0:
            crop = (PLOT[0], PLOT[1], min(WIDTH, math.ceil(X(h)) + 1), PLOT[3] + 1)
            layer = self.curve_layer.crop(crop)
            image.paste(layer, crop[:2], layer)
        d = ImageDraw.Draw(image)
        cursor = X(h)
        d.line((cursor, PLOT[1], cursor, PLOT[3]), fill="#BDCEE1", width=2)
        # The measured path itself is a staircase, matching the replay's updates.
        path = [(X(0), Y(self.rows[0]["x_rust"]))]
        for j in range(1, i + 1):
            path.append((X(self.hours[j]), Y(self.rows[j - 1]["x_rust"])))
            path.append((X(self.hours[j]), Y(self.rows[j]["x_rust"])))
        path.append((cursor, Y(row["x_rust"])))
        if len(path) > 1:
            d.line(path, fill="#A6C8EB", width=2)
        for r in self.rows[:i + 1]:
            x, y = X(r["hours"]), Y(r["x_rust"])
            d.ellipse((x - 5, y - 5, x + 5, y + 5), fill=BLUE)
        text(d, (X(0) + 14, Y(self.rows[0]["x_rust"]) - 30), "t=0 · 216× Rust", 18)
        for m in self.data["discontinuities"]:
            if m["hours"] > h:
                continue
            x, y = X(m["hours"]), Y(m["x_rust"])
            lx, ly = X(m["label_hours"]), Y(m["label_ratio"])
            annotation = f'{m["number"]} {m["label"]}'
            end = lx + d.textlength(annotation, font=font(17, True)) + 12 if m["number"] == 10 else lx - 12
            d.line((x, y, end, ly + 10), fill="#98B4D2", width=1)
            text(d, (lx, ly), annotation, 17, bold=True)
        x, y = X(row["hours"]), Y(row["x_rust"])
        d.ellipse((x - 8, y - 8, x + 8, y + 8), fill="white", outline=BLUE, width=2)
        d.ellipse((x - 4, y - 4, x + 4, y + 4), fill=BLUE)
        minutes = int(h * 60)
        text(d, (1455, 61), f'{minutes // 60:02d} h {minutes % 60:02d} m', 32, bold=True)
        # Keep numerical evidence legible while the points and balls move.
        winning = row["key"] == "paired-candidate-loads"
        d.rounded_rectangle((1215, 207, 1814, 444 if winning else 382), radius=15, fill="#F5F8FC", outline="#DEE7F1")
        text(d, (1240, 220), "MECH BEATS UNCHANGED RUST" if winning else "CURRENT MEASURED TIMING", 15, BLUE if winning else MUTED, bold=True)
        text(d, (1240, 245), f'{ratio_label(row["x_rust"])} Rust', 43, BLUE, bold=True)
        speedup = self.rows[0]["seconds"] / row["seconds"]
        gain = "Starting point" if i == 0 else f'{speedup:.0f}× faster than the start' if speedup >= 10 else f'{speedup:.1f}× faster than the start'
        if winning:
            for n, session in enumerate(s for s in self.data["final_sessions"] if s["hours"] <= h):
                text(d, (1243, 302 + n * 33), f'Session {session["session"]} · {session["seconds"]:.4f} s · {session["x_rust"]:.3f}×', 21)
            text(d, (1243, 377), gain, 20, MUTED)
            text(d, (1243, 410), "Including secured startup and shutdown", 17, MUTED)
        else:
            text(d, (1243, 302), f'{seconds_label(row["seconds"])} · full process', 23)
            text(d, (1243, 341), gain, 21, MUTED)
        label = row["label"]
        text(d, (1835, 804), f'{i + 1} / {len(self.rows)} checkpoints', 17, MUTED, anchor="ra")
        text(d, (385, 804), label, 18, MUTED)
        text(d, (85, 891), f'{row["seconds"]:.4f} s' if winning else seconds_label(row["seconds"]), 20, MUTED)
        for name in LANES:
            self.draw_ball(image, name, t)
        return image

    def verify_motion(self):
        errors = []
        jumps = []
        for i, start in enumerate(self.transitions):
            end = self.transitions[i + 1] if i + 1 < len(self.transitions) else self.duration
            a, b = start + (end - start) * .25, start + (end - start) * .75
            observed = (self.phase_at(b) - self.phase_at(a)) / (b - a)
            expected = 1 / self.trip_seconds(i)
            errors.append(abs(observed / expected - 1))
            if i:
                previous_end = self.phases[i - 1] + (start - self.transitions[i - 1]) / self.trip_seconds(i - 1)
                jumps.append(abs(previous_end - self.phases[i]))
        assert max(errors) < 1e-8
        assert max(jumps) < 1e-12
        assert self.phase_at(0) == 0
        visible = sum(0 <= h <= self.end_hour for h, _ in self.samples)
        assert visible == len(self.samples) == 732
        return {"piecewise_constant_speed_max_relative_error": max(errors),
                "phase_continuity_max_error": max(jumps),
                "retained_individual_observations": visible,
                "individual_points_drawn": 0,
                "median_points_visible_at_end": len(self.rows),
                "regressions_retained": sum(b["x_rust"] > a["x_rust"] for a, b in zip(self.rows, self.rows[1:])),
                "trend_fit_used_for_motion": False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=HERE)
    parser.add_argument("--preview-only", action="store_true")
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    replay = Replay()
    checks = replay.verify_motion()
    preview_times = [0, INTRO_SECONDS + 3.05, INTRO_SECONDS + 10, INTRO_SECONDS + 25,
                     INTRO_SECONDS + 40.6, replay.duration - 1]
    previews = []
    for n, t in enumerate(preview_times):
        image = replay.frame(t)
        image.save(out / f"frame-{n:02d}.png")
        previews.append(image.resize((960, 540), Image.Resampling.LANCZOS))
    sheet = Image.new("RGB", (1920, 1620), "white")
    for n, image in enumerate(previews):
        sheet.paste(image, ((n % 2) * 960, (n // 2) * 540))
    sheet.save(out / "contact-sheet.png")
    print(json.dumps({"preview": str(out / "contact-sheet.png"), "motion": checks}), flush=True)
    if args.preview_only:
        return
    video = out / "mech-rust-optimization-timelapse.mp4"
    silent = out / ".mech-rust-optimization-silent.mp4"
    encoder = imageio_ffmpeg.write_frames(str(silent), (WIDTH, HEIGHT), fps=FPS, codec="libx264",
        pix_fmt_in="rgb24", pix_fmt_out="yuv420p", macro_block_size=1,
        output_params=["-crf", "18", "-preset", "fast", "-threads", "2", "-movflags", "+faststart",
                       "-metadata", "title=" + " · ".join(TITLE_LINES)],
        ffmpeg_log_level="warning")
    encoder.send(None)
    try:
        for n in range(replay.frames):
            encoder.send(np.asarray(replay.frame(n / FPS)))
            if n % (FPS * 5) == 0:
                print(f"Rendered {n / FPS:.0f} / {replay.frames / FPS:.1f} seconds", flush=True)
    finally:
        encoder.close()
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    soundtrack, audio = create_soundtrack(replay, out, fps=FPS, rust_trip_seconds=RUST_TRIP_SECONDS)
    subprocess.run([ffmpeg, "-y", "-v", "error", "-i", str(silent), "-i", str(soundtrack),
        "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-ar", "48000", "-ac", "2", "-threads", "2", "-movflags", "+faststart",
        "-metadata", "title=" + " · ".join(TITLE_LINES), str(video)], check=True)
    silent.unlink()
    # A smaller silent preview is suitable for inline display as well as the MP4.
    gif = out / "mech-rust-optimization-timelapse.gif"
    subprocess.run([ffmpeg, "-y", "-v", "error", "-threads", "2", "-i", str(video),
        "-filter_complex_threads", "1", "-filter_complex",
        "fps=12,scale=960:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=128:stats_mode=diff[p];[s1][p]paletteuse=dither=bayer:bayer_scale=3",
        "-loop", "0", str(gif)], check=True)
    frames, duration = imageio_ffmpeg.count_frames_and_secs(str(video))
    assert frames == replay.frames
    assert abs(duration - frames / FPS) <= 1 / FPS
    manifest = {"schema": "mech.optimization-history-animation.v3",
        "title": " · ".join(TITLE_LINES),
        "runtime_axis_log_base": 10,
        "displayed_point_layer": "medians only", "bottom_caption": False,
        "source": str(SOURCE.relative_to(ROOT)), "source_sha256": sha(SOURCE),
        "fit_source": str(FIT_SOURCE.relative_to(ROOT)), "fit_sha256": sha(FIT_SOURCE),
        "render_source_sha256": sha(Path(__file__)), "width": WIDTH, "height": HEIGHT,
        "ball_colors": {"Mech": MECH, "Rust": RUST}, "chart_point_color": BLUE,
        "ball_animation": {"arrows": False, "maximum_horizontal_compression": .14,
                           "maximum_rebound_stretch": .04, "maximum_vertical_lift_px": 2,
                           "contact_radius_compensation": True, "sprite_supersampling": 4,
                           "motion_phase_unchanged": True},
        "audio": {"codec": "AAC", "sample_rate": audio["sample_rate"], "channels": audio["channels"],
                  "bounces": audio["bounces"], "report": "bounce-audio.json",
                  "synthesizer_sha256": audio["synthesizer_sha256"],
                  "style": audio["style"]},
        "fps": FPS, "video_frames": frames, "video_duration_seconds": duration,
        "history_duration_hours": replay.end_hour, "history_clock_speedup": HISTORY_SPEEDUP,
        "intro_seconds": INTRO_SECONDS, "outro_seconds": OUTRO_SECONDS,
        "ball_clock_rust_crossing_seconds": RUST_TRIP_SECONDS,
        "mech_crossing_formula": "1.2 * latest_measured_Mech_seconds / its_contemporaneous_Rust_median_seconds",
        "motion_update": "Hold the latest measured ratio until the next cohort's original elapsed-hour coordinate; integrate continuous position across each change.",
        "cohorts": len(replay.rows), "individual_process_observations": len(replay.samples),
        "first": {k: replay.rows[0][k] for k in ["hours", "seconds", "rust_seconds", "x_rust"]},
        "last": {k: replay.rows[-1][k] for k in ["hours", "seconds", "rust_seconds", "x_rust", "trial"]},
        "motion_verification": checks,
        "packages": {name: importlib.metadata.version(name) for name in ["matplotlib", "numpy", "Pillow", "imageio-ffmpeg"]},
        "artifacts": {p.name: {"sha256": sha(p), "bytes": p.stat().st_size} for p in
                      [video, gif, out / "contact-sheet.png", soundtrack, out / "bounce-audio.json"]},
        "notes": ["The optimization clock is linear and retains intervening gaps.",
                  "The ball clock is independently scaled so the benchmark durations remain visible.",
                  "Mech follows all 120 measured cohorts, including regressions and unpromoted trials.",
                  "The two later qualified sessions are 0.95484 and 0.96219 times unchanged Rust, at their recovered process-launch times.",
                  "The line of best fit uses all 120 measured medians and never controls ball motion. Its equation is not displayed.",
                  "All 120 median coordinates, ratios and raw seconds are unchanged; individual process observations are retained as source data but not drawn.",
                  "The bottom caption is omitted; clock definitions remain in the source documentation.",
                  "Quiet keyboard-style taps occur at the exact wall contacts: Mech lighter, Rust deeper, with subtle left/right placement.",
                  "No benchmark is rerun."]}
    (out / "animation.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"video": str(video), "gif": str(gif), "frames": frames, "duration": duration}), flush=True)


if __name__ == "__main__":
    main()
