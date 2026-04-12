#!/usr/bin/env python3

import json
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SONG_ROOT = REPO_ROOT / "songs"
OUTPUT_FILE = REPO_ROOT / "song-duration-data.js"


def format_duration(seconds: float) -> str:
    total_seconds = max(0, int(round(seconds)))
    minutes, remaining_seconds = divmod(total_seconds, 60)
    return f"{minutes}:{remaining_seconds:02d}"


def probe_duration(file_path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(file_path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return float(result.stdout.strip())


def main() -> None:
    durations = {}

    for song_file in sorted(SONG_ROOT.rglob("*.mp3")):
        relative_path = song_file.relative_to(SONG_ROOT).as_posix()
        duration_seconds = probe_duration(song_file)
        durations[relative_path] = format_duration(duration_seconds)

    output = "const SONG_DURATIONS = " + json.dumps(
        durations,
        ensure_ascii=False,
        indent=4,
        sort_keys=True,
    ) + ";\n"

    OUTPUT_FILE.write_text(output, encoding="utf-8")
    print(f"Generated {OUTPUT_FILE.relative_to(REPO_ROOT)} with {len(durations)} entries.")


if __name__ == "__main__":
    main()
