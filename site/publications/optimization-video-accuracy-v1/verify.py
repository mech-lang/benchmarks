"""Verify the published video against its pinned source commit and Pages job."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import urllib.request

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
MEDIA = "experiments/mech/native-owner-aot-v1/optimization-history-animation-v1/media-audited-60fps"
URL = "https://mech-lang.org/benchmarks/mech-compiler-optimization-60fps.mp4"
WEBSITE_COMMIT = "42db12749dc9db9329acd2b03728fc5483741ce9"
BENCHMARK_COMMIT = "bc9caf4f9374d15a8e0f513e97cc3ee30bfc945b"
PIPELINE_URL = "https://gitlab.com/api/v4/projects/5692990/pipelines/2988210204"


def source_bytes(name):
    return subprocess.check_output(["git", "show", f"{BENCHMARK_COMMIT}:{MEDIA}/{name}"], cwd=ROOT)


def main():
    with urllib.request.urlopen(PIPELINE_URL, timeout=30) as response:
        pipeline = json.load(response)
    assert pipeline["status"] == "success" and pipeline["sha"] == WEBSITE_COMMIT
    expected = source_bytes("mech-rust-optimization-timelapse.mp4")
    expected_sha = hashlib.sha256(expected).hexdigest()
    versioned_url = URL + "?v=" + WEBSITE_COMMIT[:12]
    responses = []
    for url in [versioned_url, URL]:
        request = urllib.request.Request(url, headers={"Cache-Control": "no-cache, no-store", "Pragma": "no-cache", "Accept-Encoding": "identity"})
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = response.read()
            full = {"status": response.status, "url": response.url,
                    "content_type": response.headers.get_content_type(),
                    "content_length": response.headers.get("Content-Length"),
                    "bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}
        assert full["status"] == 200 and full["content_type"] == "video/mp4"
        assert payload == expected and full["sha256"] == expected_sha, full
        responses.append(full)
    request = urllib.request.Request(versioned_url, headers={"Range": "bytes=0-1023", "Accept-Encoding": "identity"})
    with urllib.request.urlopen(request, timeout=30) as response:
        range_body = response.read()
        partial = {"status": response.status,
                   "content_range": response.headers.get("Content-Range"), "bytes": len(range_body)}
    if partial["status"] == 206:
        assert range_body == expected[:1024]
        assert partial["content_range"] == f"bytes 0-1023/{len(expected)}"
        partial["handling"] = "partial response"
    else:
        assert partial["status"] == 200 and range_body == expected
        partial["handling"] = "complete-file response"
    manifest = json.loads(source_bytes("animation.json"))
    verification = json.loads(source_bytes("encoded-verification.json"))
    assert manifest["fps"] == 60 and manifest["video_frames"] == 3426
    assert verification["intervening_60fps_frame_checked"]
    svg_url = "https://mech-lang.org/benchmarks/mech-compiler-optimization.svg?v=" + WEBSITE_COMMIT[:12]
    request = urllib.request.Request(svg_url, headers={"Accept-Encoding": "identity", "Cache-Control": "no-cache, no-store"})
    with urllib.request.urlopen(request, timeout=30) as response:
        svg_data = response.read()
        assert response.status == 200 and response.headers.get_content_type() == "image/svg+xml"
        assert svg_data == source_bytes("mech-compiler-optimization.svg")
        svg_response = {"url": svg_url, "status": response.status, "content_type": response.headers.get_content_type(),
                        "bytes": len(svg_data), "sha256": hashlib.sha256(svg_data).hexdigest()}
    audit_root = "experiments/mech/native-owner-aot-v1/optimization-history-animation-v1/accuracy-audit"
    accuracy_audit = {}
    for name, file in [("receipts", "receipt-audit.json"), ("axes", "axes.json"), ("playback", "current-release/playback-audit.json")]:
        data = json.loads(subprocess.check_output(["git", "show", f"{BENCHMARK_COMMIT}:{audit_root}/{file}"], cwd=ROOT))
        assert data["status"] == "passed"
        if name == "playback":
            assert data["video_sha256"] == expected_sha
        accuracy_audit[name] = {k: v for k, v in data.items() if k not in ["records", "clock_checkpoints", "method"]}
    report = dict(schema="mech.video-pages-deployment.v2", status="passed",
        verified_at=datetime.now(timezone.utc).isoformat(), url=URL, versioned_url=versioned_url,
        website_commit=WEBSITE_COMMIT, benchmark_source_commit=BENCHMARK_COMMIT,
        website_changes=["public/benchmarks/mech-compiler-optimization-60fps.mp4",
                         "public/benchmarks/mech-compiler-optimization.svg"],
        title=manifest["title"], video_duration_seconds=manifest["video_duration_seconds"],
        fps=manifest["fps"], video_frames=manifest["video_frames"],
        intervening_60fps_frame_checked=verification["intervening_60fps_frame_checked"],
        ball_colors=manifest["ball_colors"], audio=verification["audio"],
        impact_animation=verification["impact_animation"],
        vector_artwork=verification["vector_artwork"], svg=svg_response,
        accuracy_audit=accuracy_audit,
        pipeline={k: pipeline[k] for k in ["id", "status", "sha", "web_url", "finished_at"]},
        video=responses, byte_range=partial,
        verifier_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (HERE / "deployment.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
