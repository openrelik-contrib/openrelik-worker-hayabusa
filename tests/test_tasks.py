import os

os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from src.hayabusa import (
    DEFAULT_OUTPUT_PROFILE,
    DEFAULT_TIME_FORMAT,
    build_timeline_command,
    output_display_name,
    output_profile,
    time_format,
)
from src.csv_timeline import TASK_METADATA as CSV_TASK_METADATA
from src.html_report import TASK_METADATA as HTML_TASK_METADATA
from src.json_timeline import TASK_METADATA as JSON_TASK_METADATA


def test_default_timeline_command_uses_utc_and_standard_profile():
    command = build_timeline_command(
        "csv-timeline",
        "/tmp/out.csv",
        "/tmp/input",
        task_config={},
    )

    assert command == [
        "/hayabusa/hayabusa",
        "csv-timeline",
        "--UTC",
        "--no-wizard",
        "--quiet",
        "--profile",
        DEFAULT_OUTPUT_PROFILE,
        "--clobber",
        "--output",
        "/tmp/out.csv",
        "--directory",
        "/tmp/input",
    ]
    assert DEFAULT_TIME_FORMAT == "UTC"


def test_timeline_command_applies_time_format_and_profile_overrides():
    command = build_timeline_command(
        "json-timeline",
        "/tmp/out.json",
        "/tmp/input",
        task_config={
            "time_format": "RFC-3339",
            "output_profile": "timesketch-verbose",
        },
    )

    assert "--UTC" in command
    assert command[command.index("--profile") + 1] == "timesketch-verbose"
    assert "--RFC-3339" in command


def test_html_command_applies_profile_and_html_report_output():
    command = build_timeline_command(
        "csv-timeline",
        "/dev/null",
        "/tmp/input",
        task_config={"output_profile": "verbose"},
        html_report_path="/tmp/report.html",
    )

    assert command[command.index("--profile") + 1] == "verbose"
    assert command[command.index("--HTML-report") + 1] == "/tmp/report.html"
    assert command[command.index("--output") + 1] == "/dev/null"


def test_invalid_options_fall_back_to_shared_defaults():
    task_config = {
        "time_format": "not-a-format",
        "output_profile": "not-a-profile",
    }

    assert time_format(task_config) == DEFAULT_TIME_FORMAT
    assert output_profile(task_config) == DEFAULT_OUTPUT_PROFILE


def test_legacy_default_time_format_maps_to_utc_default():
    assert time_format({"time_format": "default"}) == DEFAULT_TIME_FORMAT


def test_output_display_name_defaults_when_not_configured():
    assert (
        output_display_name({}, "Hayabusa_CSV_timeline.csv", ".csv")
        == "Hayabusa_CSV_timeline.csv"
    )


def test_output_display_name_appends_expected_extension():
    assert (
        output_display_name(
            {"output_file_name": "case-964-hayabusa"},
            "default.csv",
            ".csv",
        )
        == "case-964-hayabusa.csv"
    )


def test_output_display_name_does_not_duplicate_expected_extension():
    assert (
        output_display_name(
            {"output_file_name": "case-964.json"},
            "default.json",
            ".json",
        )
        == "case-964.json"
    )


def test_output_display_name_uses_basename_for_path_like_values():
    assert (
        output_display_name(
            {"output_file_name": "../case-964/report"},
            "default.html",
            ".html",
        )
        == "report.html"
    )


def test_all_tasks_expose_the_same_hayabusa_options():
    assert CSV_TASK_METADATA["task_config"] == JSON_TASK_METADATA["task_config"]
    assert HTML_TASK_METADATA["task_config"] == JSON_TASK_METADATA["task_config"]
