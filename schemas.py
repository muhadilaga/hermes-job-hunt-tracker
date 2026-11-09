"""Tool schemas — what the LLM sees.

Descriptions are specific about when to use each tool. Parameters are
JSON Schema. Record only what the user states; never invent a GPA,
years of experience, or skills — the tools only store what they are given.
"""

LOG_APPLICATION = {
    "name": "job_log_application",
    "description": (
        "Log a job application the user just sent (or is about to send). "
        "Use right after an application is submitted. Rejects exact "
        "duplicates: if the same company and position were already logged, "
        "it returns an error instead of logging twice — so always call "
        "job_check_duplicate first when unsure. Dates are YYYY-MM-DD; if no "
        "follow_up_date is given it defaults to 7 days after the send date. "
        "Record only the facts the user gives; never invent a GPA, years of "
        "experience, or skills."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "company": {
                "type": "string",
                "description": "Employer name, e.g. 'PT Phincon'",
            },
            "position": {
                "type": "string",
                "description": "Job title as posted, e.g. 'Bootcamp Software Engineer'",
            },
            "channel": {
                "type": "string",
                "description": (
                    "Where it was applied: LinkedIn, Glints, JobStreet, "
                    "Email, Indeed, Dealls, Company Website, or other"
                ),
            },
            "location": {
                "type": "string",
                "description": "Job location, e.g. 'Jakarta' or 'Kab. Sleman (hybrid)'",
            },
            "status": {
                "type": "string",
                "description": "Application status; defaults to Sent",
                "enum": ["Sent", "In Progress", "Rejected", "Interview", "Accepted"],
            },
            "date": {
                "type": "string",
                "description": "Date sent, YYYY-MM-DD; defaults to today",
            },
            "follow_up_date": {
                "type": "string",
                "description": "Follow-up date, YYYY-MM-DD; defaults to 7 days after the send date",
            },
            "notes": {
                "type": "string",
                "description": "Anything worth remembering about this application",
            },
        },
        "required": ["company", "position"],
    },
}

LIST_APPLICATIONS = {
    "name": "job_list_applications",
    "description": (
        "List logged job applications, newest first. Use when the user asks "
        "what they have applied to, or wants to review applications by "
        "status or channel."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "status": {
                "type": "string",
                "description": "Filter by status",
                "enum": ["Sent", "In Progress", "Rejected", "Interview", "Accepted"],
            },
            "channel": {
                "type": "string",
                "description": "Filter by channel, e.g. 'JobStreet' or 'Glints'",
            },
        },
        "required": [],
    },
}

CHECK_DUPLICATE = {
    "name": "job_check_duplicate",
    "description": (
        "Check whether the user already applied to a company and position. "
        "Call this BEFORE logging a new application or before applying to a "
        "lead, to avoid applying twice to the same role. Matching is "
        "case-insensitive on company and position."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "company": {
                "type": "string",
                "description": "Employer name to check",
            },
            "position": {
                "type": "string",
                "description": "Job title to check",
            },
        },
        "required": ["company", "position"],
    },
}

UPDATE_STATUS = {
    "name": "job_update_status",
    "description": (
        "Update the status of a logged application — for example when a "
        "reply arrives, an interview is scheduled, or an application is "
        "rejected. The application must already be logged; if it is not "
        "found, log it first with job_log_application."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "company": {
                "type": "string",
                "description": "Employer name of the logged application",
            },
            "position": {
                "type": "string",
                "description": "Job title of the logged application",
            },
            "new_status": {
                "type": "string",
                "description": "The new status",
                "enum": ["Sent", "In Progress", "Rejected", "Interview", "Accepted"],
            },
            "notes": {
                "type": "string",
                "description": "Optional notes to store with the application (replaces existing notes)",
            },
        },
        "required": ["company", "position", "new_status"],
    },
}

FOLLOWUPS_DUE = {
    "name": "job_followups_due",
    "description": (
        "List applications whose follow-up date falls within the next N days "
        "or is already overdue, earliest first. Use when the user asks what "
        "to follow up on. Rejected and accepted applications are excluded — "
        "they need no follow-up."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "within_days": {
                "type": "integer",
                "description": "How many days ahead to look; defaults to 7",
                "default": 7,
            },
        },
        "required": [],
    },
}

APPLICATION_STATS = {
    "name": "job_application_stats",
    "description": (
        "Summarise the job hunt: total applications logged, counts by "
        "status and by channel. Use when the user asks for an overview or "
        "how the hunt is going."
    ),
    "parameters": {
        "type": "object",
        "properties": {},
        "required": [],
    },
}
