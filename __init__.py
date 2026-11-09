"""job-hunt-tracker plugin — registration."""

import logging
from pathlib import Path

from . import schemas, tools

logger = logging.getLogger(__name__)

_TOOLSET = "job_hunt_tracker"

_TOOLS = (
    ("job_log_application", schemas.LOG_APPLICATION, tools.job_log_application),
    ("job_list_applications", schemas.LIST_APPLICATIONS, tools.job_list_applications),
    ("job_check_duplicate", schemas.CHECK_DUPLICATE, tools.job_check_duplicate),
    ("job_update_status", schemas.UPDATE_STATUS, tools.job_update_status),
    ("job_followups_due", schemas.FOLLOWUPS_DUE, tools.job_followups_due),
    ("job_application_stats", schemas.APPLICATION_STATS, tools.job_application_stats),
)


def register(ctx):
    """Wire schemas to handlers and register the bundled skill."""
    for name, schema, handler in _TOOLS:
        ctx.register_tool(name=name, toolset=_TOOLSET, schema=schema, handler=handler)

    skills_dir = Path(__file__).parent / "skills"
    if skills_dir.is_dir():
        for child in sorted(skills_dir.iterdir()):
            skill_md = child / "SKILL.md"
            if child.is_dir() and skill_md.exists():
                ctx.register_skill(child.name, skill_md)

    logger.debug("job-hunt-tracker registered: %d tools", len(_TOOLS))
