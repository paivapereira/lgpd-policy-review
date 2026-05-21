"""Synthetic fixture — false positive control: UUIDs, ISO date ranges, and
order numbers with digit-and-hyphen formats neighboring the BR identifier
formats.

Recognizer rules MUST NOT match this snippet because none of the strings
follow a canonical BR identifier format precisely AND the variable names
are not identifier-related.

This negative exercises AS-7 of T07.
"""

RESOURCE_ID = "12345678-9012-3456-7890-123456789012"  # UUID v4-like
TRACE_ID = "550e8400-e29b-41d4-a716-446655440000"  # canonical UUID v4
DATE_RANGE = "2024-01-15-2024-12-31"  # ISO date range
ORDER_NUMBER = "ORD-2024-001-238547961"  # internal order numbering


def get_resource_metadata() -> dict:
    """Return resource metadata. Does not collect identifiers."""
    return {
        "id": RESOURCE_ID,
        "trace": TRACE_ID,
        "valid_range": DATE_RANGE,
        "order": ORDER_NUMBER,
    }
