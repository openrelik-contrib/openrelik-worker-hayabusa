HAYABUSA_BINARY = "/hayabusa/hayabusa"

DEFAULT_OUTPUT_PROFILE = "standard"
DEFAULT_TIME_FORMAT = "UTC"

OUTPUT_PROFILES = [
    "minimal",
    "standard",
    "verbose",
    "all-field-info",
    "all-field-info-verbose",
    "super-verbose",
    "timesketch-minimal",
    "timesketch-verbose",
]

TIME_FORMAT_FLAGS = {
    "UTC": None,
    "default": None,
    "ISO-8601": "--ISO-8601",
    "RFC-2822": "--RFC-2822",
    "RFC-3339": "--RFC-3339",
}

TIME_FORMATS = [
    "UTC",
    "ISO-8601",
    "RFC-2822",
    "RFC-3339",
]


def timeline_task_config() -> list[dict[str, object]]:
    return [
        {
            "name": "time_format",
            "label": "Time format",
            "description": (
                "Output timestamps in UTC by default, or choose a specific "
                "Hayabusa timestamp format."
            ),
            "type": "select",
            "items": list(TIME_FORMATS),
            "default": DEFAULT_TIME_FORMAT,
            "required": False,
        },
        {
            "name": "output_profile",
            "label": "Output profile",
            "description": "Hayabusa output profile.",
            "type": "select",
            "items": list(OUTPUT_PROFILES),
            "default": DEFAULT_OUTPUT_PROFILE,
            "required": False,
        },
        {
            "name": "output_file_name",
            "label": "Output file name",
            "description": "Custom output file name.",
            "type": "text",
            "required": False,
        },
    ]


def _config_value(task_config: dict | None, key: str, default: str) -> str:
    if not isinstance(task_config, dict):
        return default
    value = (task_config or {}).get(key, default)
    if isinstance(value, list):
        value = value[0] if value else default
    if value is None or value == "":
        return default
    return str(value)


def output_profile(task_config: dict | None) -> str:
    profile = _config_value(task_config, "output_profile", DEFAULT_OUTPUT_PROFILE)
    if profile not in OUTPUT_PROFILES:
        return DEFAULT_OUTPUT_PROFILE
    return profile


def time_format(task_config: dict | None) -> str:
    selected_format = _config_value(task_config, "time_format", DEFAULT_TIME_FORMAT)
    if selected_format not in TIME_FORMAT_FLAGS:
        return DEFAULT_TIME_FORMAT
    if selected_format == "default":
        return DEFAULT_TIME_FORMAT
    return selected_format


def output_display_name(
    task_config: dict | None,
    default_display_name: str,
    extension: str,
) -> str:
    display_name = _config_value(task_config, "output_file_name", "")
    if not display_name:
        return default_display_name

    display_name = display_name.strip().replace("\\", "/").split("/")[-1]
    if not display_name or display_name in {".", ".."}:
        return default_display_name

    normalized_extension = "." + extension.lstrip(".")
    if display_name.lower().endswith(normalized_extension.lower()):
        display_name = display_name[: -len(normalized_extension)]

    if not display_name:
        return default_display_name
    return f"{display_name}{normalized_extension}"


def build_timeline_command(
    subcommand: str,
    output_path: str,
    input_directory: str,
    task_config: dict | None,
    html_report_path: str | None = None,
) -> list[str]:
    command = [
        HAYABUSA_BINARY,
        subcommand,
        "--UTC",
        "--no-wizard",
        "--quiet",
        "--profile",
        output_profile(task_config),
    ]

    selected_time_format = time_format(task_config)
    time_format_flag = TIME_FORMAT_FLAGS[selected_time_format]
    if time_format_flag:
        command.append(time_format_flag)

    command.append("--clobber")

    if html_report_path:
        command.extend(["--HTML-report", html_report_path])

    command.extend(
        [
            "--output",
            output_path,
            "--directory",
            input_directory,
        ]
    )
    return command
