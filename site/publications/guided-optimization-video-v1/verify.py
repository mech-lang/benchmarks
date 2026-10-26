"""Verify the published MP4 by complete hash, content type and HTTP responses."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import urllib.request

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
VIDEO = ROOT / "experiments/mech/native-owner-aot-v1/optimization-history-animation-v1/media/mech-rust-optimization-timelapse.mp4"
URL = "https://mech-lang.org/benchmarks/mech-guided-llm-optimization.mp4"
WEBSITE_COMMIT = "dd7da2e2b3bd92780b54b3b9d3c7b81d47d46b99"
BENCHMARK_COMMIT = "0c3f859a142941bc4e3a2154915032510a075f6f"
PIPELINE_URL = "https://gitlab.com/api/v4/projects/5692990/pipelines/2987851244"


def main():
    with urllib.request.urlopen(PIPELINE_URL, timeout=30) as response:
        pipeline = json.load(response)
    assert pipeline["status"] == "success" and pipeline["sha"] == WEBSITE_COMMIT
    expected = VIDEO.read_bytes()
    expected_sha = hashlib.sha256(expected).hexdigest()
    request = urllib.request.Request(URL, headers={"Cache-Control": "no-cache", "Accept-Encoding": "identity"})
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = response.read()
        full = {"status": response.status, "url": response.url,
                "content_type": response.headers.get_content_type(),
                "content_length": response.headers.get("Content-Length"),
                "bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}
    assert full["status"] == 200 and full["content_type"] == "video/mp4"
    assert payload == expected and full["sha256"] == expected_sha
    request = urllib.request.Request(URL, headers={"Range": "bytes=0-1023", "Accept-Encoding": "identity"})
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
    manifest = json.loads((VIDEO.parent / "animation.json").read_text())
    report = dict(schema="mech.video-pages-deployment.v1", status="passed",
        verified_at=datetime.now(timezone.utc).isoformat(), url=URL,
        website_commit=WEBSITE_COMMIT, benchmark_source_commit=BENCHMARK_COMMIT,
        website_changes=["public/benchmarks/mech-guided-llm-optimization.mp4"],
        title=manifest["title"], video_duration_seconds=manifest["video_duration_seconds"],
        pipeline={k: pipeline[k] for k in ["id", "status", "sha", "web_url", "finished_at"]},
        video=full, byte_range=partial,
        verifier_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (HERE / "deployment.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
