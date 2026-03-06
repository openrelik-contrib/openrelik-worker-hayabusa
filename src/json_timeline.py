import os
import shutil
import subprocess
import time
from uuid import uuid4

from openrelik_worker_common.file_utils import create_output_file
from openrelik_worker_common.task_utils import create_task_result, get_input_files

from .app import celery

# Task name used to register and route the task to the correct queue.
TASK_NAME = "openrelik-worker-hayabusa.tasks.json_timeline"

# Task metadata for registration in the core system.
TASK_METADATA = {
    "display_name": "Hayabusa JSON timeline",
    "description": "Windows event log triage",
    "task_config": [
        {
            "name": "time_format",
            "label": "Default is YYYY-MM-DD HH:mm:ss.sss +hh:mm",
            "description": "Time format",
            "type": "select",
            "items": [ "default", "ISO-8601", "RFC-2822", "RFC-3339" ],
            "required": False,
        },
        {
            "name": "output_profile",
            "label": "Choose an output profile",
            "description": "Output profile",
            "type": "select",
            "items": [ "minimal", "standard", "verbose", "all-field-info", "all-field-info-verbose", "super-verbose", "timesketch-minimal", "timesketch-verbose" ],
            "required": False,
        },
    ],
}

COMPATIBLE_INPUTS = {
    "data_types": [],
    "mime_types": ["application/x-ms-evtx"],
    "filenames": ["*.evtx"],
}


@celery.task(bind=True, name=TASK_NAME, metadata=TASK_METADATA)
def csv_timeline(
    self,
    pipe_result=None,
    input_files=[],
    output_path=None,
    workflow_id=None,
    task_config={},
) -> str:
    output_files = []
    input_files = get_input_files(pipe_result, input_files or [], filter=COMPATIBLE_INPUTS)
    if not input_files:
        return create_task_result(
            output_files=output_files,
            workflow_id=workflow_id,
            command="",
        )

    output_file = create_output_file(
        output_path,
        display_name="Hayabusa_JSON_timeline.json",
        data_type="openrelik:hayabusa:json_timeline",
    )

    # Create temporary directory and hard link files for processing
    temp_dir = os.path.join(output_path, uuid4().hex)
    os.mkdir(temp_dir)
    for file in input_files:
        filename = os.path.basename(file.get("path"))
        os.link(file.get("path"), f"{temp_dir}/{filename}")

    time_format = task_config.get("time_format", "default")
    output_profile = task_config.get("output_profile", "standard")

    if time_format == "default":
        command = [
            "/hayabusa/hayabusa",
            "json-timeline",
            "--UTC",
            "--no-wizard",
            "--quiet",
            "--profile",
            output_profile,
            "--clobber",
            "--output",
            output_file.path,
            "--directory",
            temp_dir,
        ]
    else:
        time_format_param = "--" + time_format
        command = [
            "/hayabusa/hayabusa",
            "json-timeline",
            time_format_param,
            "--UTC",
            "--no-wizard",
            "--quiet",
            "--profile",
            output_profile,
            "--clobber",
            "--output",
            output_file.path,
            "--directory",
            temp_dir,
        ]

    INTERVAL_SECONDS = 2
    process = subprocess.Popen(command)
    while process.poll() is None:
        self.send_event("task-progress", data=None)
        time.sleep(INTERVAL_SECONDS)

    # Remove temp directory
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)

    output_files.append(output_file.to_dict())

    return create_task_result(
        output_files=output_files,
        workflow_id=workflow_id,
        command=" ".join(command),
    )
