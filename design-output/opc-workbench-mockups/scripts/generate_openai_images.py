#!/usr/bin/env python3
"""Generate OPC mockup PNGs from prompts.json via an OpenAI-compatible image API."""

from __future__ import annotations

import argparse
import base64
import json
import os
import struct
import sys
import time
from pathlib import Path
from typing import Any

import requests


DEFAULT_ENDPOINT = "https://ai.input.im/v1/images/generations"
DEFAULT_MODEL = "gpt-image-2"
DEFAULT_SIZE = "2048x1152"
DEFAULT_QUALITY = "high"
DEFAULT_OUTPUT_FORMAT = "png"

COMPACT_STYLE_PROMPT = (
    "Create one high-fidelity 16:9 desktop browser UI screenshot for 新商机 OPC社区. "
    "Match the supplied reference style strictly: gray browser tab bar, large handwritten red-and-gold 新商机 OPC社区 logo, long rounded purple search box, dark navy VIP pill, bold Chinese top channel tabs with purple active underline, pale blue-gray background, dense white 8px cards, subtle borders, crisp blue-purple line icons, red-orange promo panel, gold VIP accents, teal status chips, and slate text. "
    "Use simplified Chinese UI labels only. "
    "Do not create a generic SaaS dashboard, admin console, landing page, dark theme, poster, hero illustration, stock-photo layout, cartoon mascot, decorative blobs, or a new logo."
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate OPC workbench mockup images from prompt files."
    )
    parser.add_argument("--work-dir", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--endpoint", default=os.getenv("OPC_IMAGE_ENDPOINT", DEFAULT_ENDPOINT))
    parser.add_argument("--model", default=os.getenv("OPC_IMAGE_MODEL", DEFAULT_MODEL))
    parser.add_argument("--size", default=os.getenv("OPC_IMAGE_SIZE", DEFAULT_SIZE))
    parser.add_argument("--quality", default=os.getenv("OPC_IMAGE_QUALITY", DEFAULT_QUALITY))
    parser.add_argument(
        "--output-format",
        default=os.getenv("OPC_IMAGE_OUTPUT_FORMAT", DEFAULT_OUTPUT_FORMAT),
    )
    parser.add_argument(
        "--prompt-mode",
        choices=("compact", "full"),
        default=os.getenv("OPC_IMAGE_PROMPT_MODE", "compact"),
        help="Use compact prompts by default for a more stable gateway request.",
    )
    parser.add_argument("--max-attempts", type=int, default=int(os.getenv("OPC_IMAGE_MAX_ATTEMPTS", "3")))
    parser.add_argument("--retry-delay", type=float, default=float(os.getenv("OPC_IMAGE_RETRY_DELAY", "8")))
    parser.add_argument("--sleep-seconds", type=float, default=float(os.getenv("OPC_IMAGE_SLEEP_SECONDS", "2")))
    parser.add_argument("--force", action="store_true", help="Regenerate images that already exist.")
    parser.add_argument(
        "--only",
        action="append",
        default=[],
        help="Generate only matching mockup id or filename. Can be repeated.",
    )
    parser.add_argument("--limit", type=int, default=0, help="Generate at most N remaining images.")
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        raise SystemExit(f"Missing file: {path}")
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {path}: {exc}") from exc


def read_full_prompt(work_dir: Path, prompt_files: list[str]) -> str:
    parts: list[str] = []
    for prompt_file in prompt_files:
        path = work_dir / prompt_file
        try:
            parts.append(path.read_text(encoding="utf-8-sig").strip())
        except FileNotFoundError:
            raise SystemExit(f"Missing prompt file: {path}")
    prompt = "\n\n".join(part for part in parts if part)
    prompt += (
        "\n\nGeneration requirements:\n"
        "- Output exactly one high-fidelity desktop SaaS UI mockup screenshot.\n"
        "- Use simplified Chinese UI copy inside the interface.\n"
        "- Keep the browser shell, top navigation, left sidebar, white cards, dense tables, queues, and purple-blue primary accents.\n"
        "- Avoid marketing hero posters, decorative blobs, dark theme, watermarks, and empty generic dashboards.\n"
        "- The image must be a complete 16:9 desktop screenshot."
    )
    return prompt


def read_page_prompt_summary(work_dir: Path, prompt_files: list[str]) -> str:
    page_files = [item for item in prompt_files if item.replace("\\", "/").startswith("prompts/")]
    if not page_files:
        return ""
    path = work_dir / page_files[-1]
    try:
        text = path.read_text(encoding="utf-8-sig")
    except FileNotFoundError:
        raise SystemExit(f"Missing prompt file: {path}")
    useful_lines: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("- "):
            useful_lines.append(line[2:])
        elif line.lower().startswith(("page:", "render", "main content title:", "subtitle:", "mood:")):
            useful_lines.append(line)
        if len(" ".join(useful_lines)) > 700:
            break
    return " ".join(useful_lines)


def build_compact_prompt(work_dir: Path, job: dict[str, Any]) -> str:
    modules = ", ".join(str(item) for item in job.get("keyModules", []))
    page_summary = read_page_prompt_summary(work_dir, list(job["promptFiles"]))
    return (
        f"{COMPACT_STYLE_PROMPT}\n"
        f"Page target: {job.get('pageTarget', job.get('id', 'OPC workbench page'))}.\n"
        f"Required modules: {modules}.\n"
        f"Page-specific layout notes: {page_summary}\n"
        "Make this screen clearly different from the other OPC pages through its module structure, while keeping the same design system."
    )


def build_prompt(work_dir: Path, job: dict[str, Any], mode: str) -> str:
    if mode == "full":
        return read_full_prompt(work_dir, list(job["promptFiles"]))
    return build_compact_prompt(work_dir, job)


def png_dimensions(raw: bytes) -> tuple[int | None, int | None]:
    if raw.startswith(b"\x89PNG\r\n\x1a\n") and len(raw) >= 24:
        return struct.unpack(">II", raw[16:24])
    return None, None


def decode_image_response(session: requests.Session, data: dict[str, Any]) -> bytes:
    items = data.get("data") or []
    if not items:
        raise RuntimeError("response has no data items")
    first = items[0]
    if "b64_json" in first:
        return base64.b64decode(first["b64_json"])
    if "url" in first:
        response = session.get(first["url"], timeout=180)
        response.raise_for_status()
        return response.content
    raise RuntimeError(f"response image item has unsupported keys: {sorted(first.keys())}")


def request_image(
    *,
    session: requests.Session,
    endpoint: str,
    api_key: str,
    payload: dict[str, Any],
    attempts: int,
    retry_delay: float,
    label: str,
) -> bytes:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            response = session.post(endpoint, headers=headers, json=payload, timeout=240)
            if response.status_code >= 500:
                raise RuntimeError(f"HTTP {response.status_code}: {response.text[:300]}")
            if response.status_code >= 400:
                raise RuntimeError(f"HTTP {response.status_code}: {response.text[:800]}")
            return decode_image_response(session, response.json())
        except Exception as exc:  # noqa: BLE001 - keep retry handling broad for gateway flakes.
            last_error = exc
            print(f"{label} attempt {attempt}/{attempts} failed: {exc}", file=sys.stderr)
            if attempt < attempts:
                time.sleep(retry_delay * attempt)
    raise RuntimeError(f"{label} failed after {attempts} attempts: {last_error}")


def selected(job: dict[str, Any], filters: set[str]) -> bool:
    if not filters:
        return True
    values = {
        str(job.get("id", "")).lower(),
        str(job.get("filename", "")).lower(),
        Path(str(job.get("filename", ""))).stem.lower(),
    }
    return bool(values & filters)


def main() -> int:
    args = parse_args()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("OPENAI_API_KEY is not set.")

    work_dir = Path(args.work_dir).resolve()
    index = load_json(work_dir / "prompts.json")
    filters = {item.strip().lower() for item in args.only if item.strip()}

    jobs: list[dict[str, Any]] = []
    for job in index.get("mockups", []):
        if not selected(job, filters):
            continue
        output = work_dir / str(job["filename"])
        if output.exists() and not args.force:
            print(f"skip existing: {output.name}")
            continue
        jobs.append(job)
        if args.limit and len(jobs) >= args.limit:
            break

    if not jobs:
        print("No images to generate.")
        return 0

    session = requests.Session()
    session.trust_env = False

    print(f"Endpoint: {args.endpoint}")
    print(f"Model: {args.model}, size: {args.size}, quality: {args.quality}")
    print(f"Prompt mode: {args.prompt_mode}")
    print(f"Generating {len(jobs)} image(s) into {work_dir}")

    failures: list[tuple[str, str]] = []
    for index_no, job in enumerate(jobs, start=1):
        label = f"[{index_no}/{len(jobs)} {job['id']}]"
        output = work_dir / str(job["filename"])
        prompt = build_prompt(work_dir, job, args.prompt_mode)
        payload = {
            "model": args.model,
            "prompt": prompt,
            "size": args.size,
            "quality": args.quality,
            "output_format": args.output_format,
            "n": 1,
        }
        started = time.time()
        print(f"{label} starting -> {output.name}", flush=True)
        try:
            raw = request_image(
                session=session,
                endpoint=args.endpoint,
                api_key=api_key,
                payload=payload,
                attempts=args.max_attempts,
                retry_delay=args.retry_delay,
                label=label,
            )
            output.parent.mkdir(parents=True, exist_ok=True)
            tmp_output = output.with_suffix(output.suffix + ".part")
            tmp_output.write_bytes(raw)
            tmp_output.replace(output)
            width, height = png_dimensions(raw)
            elapsed = time.time() - started
            print(
                f"{label} wrote {output.name} ({len(raw)} bytes, {width}x{height}, {elapsed:.1f}s)",
                flush=True,
            )
        except Exception as exc:  # noqa: BLE001 - collect failures and continue the batch.
            failures.append((str(job.get("id", output.name)), str(exc)))
            print(f"{label} failed: {exc}", file=sys.stderr, flush=True)
        if args.sleep_seconds > 0 and index_no < len(jobs):
            time.sleep(args.sleep_seconds)

    if failures:
        print("Failed jobs:", file=sys.stderr)
        for job_id, error in failures:
            print(f"- {job_id}: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
