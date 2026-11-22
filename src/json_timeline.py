import os
import shutil
from uuid import uuid4

from openrelik_worker_common.file_utils import create_output_file
from openrelik_worker_common.task_utils import create_task_result, get_input_files

from .app import celery
from .hayabusa import (
    build_timeline_command,
    link_inputs,
    output_display_name,
    run_hayabusa,
    timeline_task_config,
)

# Task name used to register and route the task to the correct queue.
TASK_NAME = "openrelik-worker-hayabusa.tasks.json_timeline"
DEFAULT_DISPLAY_NAME = "Hayabusa_JSON_timeline.json"

# Task metadata for registration in the core system.
TASK_METADATA = {
    "display_name": "Hayabusa JSON timeline",
    "description": "Windows event log triage",
    "task_config": timeline_task_config(),
}

COMPATIBLE_INPUTS = {
    "data_types": [],
    "mime_types": ["application/x-ms-evtx"],
    "filenames": ["*.evtx"],
}


@celery.task(bind=True, name=TASK_NAME, metadata=TASK_METADATA)
def json_timeline(
    self,
    pipe_result=None,
    input_files=None,
    output_path=None,
    workflow_id=None,
    task_config=None,
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
        display_name=output_display_name(task_config, DEFAULT_DISPLAY_NAME, ".json"),
        data_type="openrelik:hayabusa:json",
    )

    # Create temporary directory and hard link files for processing
    temp_dir = os.path.join(output_path, uuid4().hex)
    os.mkdir(temp_dir)
    link_inputs(input_files, temp_dir)

    command = build_timeline_command(
        "json",
        output_file.path,
        temp_dir,
        task_config,
    )

    run_hayabusa(self, command)

    # Remove temp directory
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)

    output_files.append(output_file.to_dict())

    return create_task_result(
        output_files=output_files,
        workflow_id=workflow_id,
        command=" ".join(command),
    )
