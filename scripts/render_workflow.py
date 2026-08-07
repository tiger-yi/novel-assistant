import argparse
from pathlib import Path
import sys

try:
    from scripts.harness_runtime import HarnessManifest
except ModuleNotFoundError:  # Direct script execution.
    from harness_runtime import HarnessManifest


def render_pipeline(manifest: dict, pipeline_name: str) -> str:
    pipeline = (manifest.get("pipelines") or {}).get(pipeline_name)
    if not isinstance(pipeline, dict):
        raise ValueError(f"unknown pipeline: {pipeline_name}")
    stages = pipeline.get("stages") or []
    lines = [
        f"# Pipeline: {pipeline_name}",
        "",
        "| 顺序 | 阶段 | 规范 | 处理器 | 要求 |",
        "| :--- | :--- | :--- | :--- | :--- |",
    ]
    for index, stage in enumerate(stages, start=1):
        requirement = "必需" if stage.get("required") else "可选"
        lines.append(
            f"| {index} | `{stage.get('name')}` | `{stage.get('uses')}` | "
            f"`{stage.get('handler')}` | {requirement} |"
        )

    lines.extend(["", "```mermaid", "flowchart TD"])
    for index, stage in enumerate(stages, start=1):
        requirement = "必需" if stage.get("required") else "可选"
        lines.append(f'    S{index}["{stage.get("name")} ({requirement})"]')
        if index > 1:
            lines.append(f"    S{index - 1} --> S{index}")
    lines.extend(["```", ""])
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Render a Manifest pipeline")
    parser.add_argument("pipeline")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=(
            Path(__file__).resolve().parents[1]
            / "novel-harness"
            / "context.manifest.yaml"
        ),
    )
    args = parser.parse_args(argv)
    try:
        manifest = HarnessManifest.load(args.manifest)
        print(render_pipeline(manifest.data, args.pipeline), end="")
    except (OSError, ValueError) as exc:
        print(f"[FAIL] {exc}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
