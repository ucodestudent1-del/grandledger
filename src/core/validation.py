"""Input validation utilities for passwords and other user data."""
from __future__ import annotations

import re


def validate_password_strength(password: str) -> tuple[bool, str]:
    """Validate password meets minimum security requirements.

    Returns (is_valid, message).
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if len(password) > 128:
        return False, "Password must be at most 128 characters long"
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one digit"
    return True, ""


def validate_email(email: str) -> tuple[bool, str]:
    """Basic email format validation."""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(pattern, email):
        return False, "Invalid email format"
    return True, ""


def validate_company_slug(slug: str) -> tuple[bool, str]:
    """Validate company slug format (lowercase, hyphens, alphanumeric)."""
    if not slug:
        return False, "Slug is required"
    if len(slug) < 3:
        return False, "Slug must be at least 3 characters"
    if not re.match(r"^[a-z0-9-]+$", slug):
        return False, "Slug must contain only lowercase letters, numbers, and hyphens"
    if slug.startswith("-") or slug.endswith("-"):
        return False, "Slug must not start or end with a hyphen"
    return True, ""
