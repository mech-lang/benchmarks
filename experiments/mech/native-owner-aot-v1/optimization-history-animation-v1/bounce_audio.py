#!/usr/bin/env python3
"""Synthesize quiet keyboard-style impacts at the replay's exact wall contacts."""
import hashlib
import json
import math
from pathlib import Path
import subprocess
import tempfile
import wave

import imageio_ffmpeg
import numpy as np

SAMPLE_RATE = 48000
SEED = 20261026


def bounce_events(replay, *, fps, rust_trip_seconds):
    duration = replay.frames / fps
    events = []
    for k in range(1, math.ceil(duration / rust_trip_seconds)):
        events.append(dict(language="Rust", time_seconds=k * rust_trip_seconds, crossing=k,
                           wall="right" if k % 2 else "left"))
    crossing = 1
    for i, start in enumerate(replay.transitions):
        end = replay.transitions[i + 1] if i + 1 < len(replay.transitions) else duration
        phase_start = replay.phases[i]
        phase_end = phase_start + (end - start) / replay.trip_seconds(i)
        while crossing <= phase_end + 1e-12:
            t = start + (crossing - phase_start) * replay.trip_seconds(i)
            assert start - 1e-8 <= t <= end + 1e-8
            assert abs(replay.phase_at(t) - crossing) < 1e-8
            if t < duration:
                events.append(dict(language="Mech", time_seconds=t, crossing=crossing,
                                   wall="right" if crossing % 2 else "left"))
            crossing += 1
    events.sort(key=lambda e: (e["time_seconds"], e["language"]))
    return events


def smooth_noise(rng, n, sigma):
    radius = math.ceil(sigma * 4)
    x = np.arange(-radius, radius + 1)
    kernel = np.exp(-.5 * (x / sigma) ** 2)
    kernel /= kernel.sum()
    noise = np.convolve(rng.standard_normal(n), kernel, mode="same")
    return noise / max(float(np.std(noise)), 1e-9)


def key_tap(language, rng):
    # Very short, damped wood-like resonances and filtered felt-like noise.
    # The rounded attack and low-pass transient avoid a sharp digital beep.
    mech = language == "Mech"
    duration = .085 if mech else .105
    n = round(duration * SAMPLE_RATE)
    t = np.arange(n) / SAMPLE_RATE
    pitch = (410 if mech else 265) * rng.uniform(.98, 1.02)
    low = smooth_noise(rng, n, 10 if mech else 16)
    upper = smooth_noise(rng, n, 4) - .5 * smooth_noise(rng, n, 14)
    attack = 1 - np.exp(-t / .0016)
    resonant = (.40 * np.sin(2 * np.pi * pitch * t) * np.exp(-t / .014)
                + .17 * np.sin(2 * np.pi * pitch * 2.13 * t + .3) * np.exp(-t / .008))
    felt = .52 * low * np.exp(-t / (.010 if mech else .014))
    touch = .065 * upper * np.exp(-t / .0035)
    tap = attack * (resonant + felt + touch)
    fade = min(n, round(.012 * SAMPLE_RATE))
    tap[-fade:] *= np.linspace(1, 0, fade) ** 2
    tap -= tap.mean()
    # Tapering also removes the tiny DC-correction endpoint discontinuity.
    edge = round(.0015 * SAMPLE_RATE)
    tap[:edge] *= np.linspace(0, 1, edge)
    tap[-edge:] *= np.linspace(1, 0, edge)
    tap /= max(float(np.abs(tap).max()), 1e-9)
    return tap * (.105 if mech else .100) * rng.uniform(.97, 1.03)


def create_soundtrack(replay, out, *, fps, rust_trip_seconds):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    duration = replay.frames / fps
    samples = round(duration * SAMPLE_RATE)
    audio = np.zeros((samples, 2), dtype=np.float64)
    events = bounce_events(replay, fps=fps, rust_trip_seconds=rust_trip_seconds)
    rng = np.random.default_rng(SEED)
    for event in events:
        tap = key_tap(event["language"], rng)
        start = round(event["time_seconds"] * SAMPLE_RATE)
        available = min(len(tap), samples - start)
        # Subtle spatial placement follows the physical wall, without hard pans.
        pan = .16 if event["wall"] == "right" else -.16
        gains = np.sqrt(np.array([(1 - pan) / 2, (1 + pan) / 2]))
        audio[start:start + available] += tap[:available, None] * gains
        event["sample"] = start
        event["pan"] = pan
    peak = float(np.abs(audio).max())
    if peak > .16:
        audio *= .16 / peak
    peak = float(np.abs(audio).max())
    rms = float(np.sqrt(np.mean(audio * audio)))
    assert peak < .17 and rms < .025
    pcm = np.round(np.clip(audio, -1, 1) * 32767).astype("<i2")
    path = out / "bounce-soundtrack.flac"
    with tempfile.TemporaryDirectory(prefix="mech-bounce-audio-") as temp:
        wav = Path(temp) / "bounce-soundtrack.wav"
        with wave.open(str(wav), "wb") as w:
            w.setnchannels(2)
            w.setsampwidth(2)
            w.setframerate(SAMPLE_RATE)
            w.writeframes(pcm.tobytes())
        subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-v", "error", "-i", str(wav),
                        "-c:a", "flac", "-compression_level", "8", "-threads", "2", str(path)], check=True)
    report = dict(schema="mech.bounce-audio.v1", sample_rate=SAMPLE_RATE, channels=2,
        samples=samples, duration_seconds=duration, seed=SEED,
        style="Quiet rounded keyboard-style impacts; Mech lighter, Rust deeper; no music or sustained beeps.",
        peak_dbfs=20 * math.log10(peak), rms_dbfs=20 * math.log10(rms),
        maximum_absolute_sample=peak,
        bounces={name: sum(e["language"] == name for e in events) for name in ["Mech", "Rust"]},
        events=events, soundtrack_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        pcm_sha256=hashlib.sha256(pcm.tobytes()).hexdigest(),
        synthesizer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (out / "bounce-audio.json").write_text(json.dumps(report, indent=2) + "\n")
    return path, report
