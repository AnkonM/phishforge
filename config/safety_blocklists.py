"""
PhishForge safety blocklists and pattern definitions.

Source of truth: Document B v2 §11.
Populated in Phase 3 (Safety Gate).

Note: The brand and keyword blocklists below represent a solid, checkable baseline
of common real-world phishing impersonation targets. They are documented as
non-exhaustive and should be augmented according to organizational threat models.
"""

from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# 1. Real Brand & Organization Blocklist (Non-exhaustive representative set)
# ---------------------------------------------------------------------------

BLOCKED_BRANDS: list[str] = [
    # Major Tech & Cloud Services
    "microsoft",
    "office 365",
    "office365",
    "microsoft 365",
    "azure",
    "outlook",
    "google",
    "gmail",
    "google drive",
    "google workspace",
    "apple",
    "icloud",
    "amazon",
    "aws",
    "dropbox",
    "docusign",
    "adobe",
    "salesforce",
    "slack",
    "zoom",
    "github",
    "linkedin",
    "cisco",
    "oracle",
    "sap",  # Note: SAP in enterprise context should not be impersonated as SAP Inc.
    
    # Financial & Payment Services
    "paypal",
    "stripe",
    "square",
    "venmo",
    "zelle",
    "chase",
    "jpmorgan",
    "bank of america",
    "wells fargo",
    "citibank",
    "citi",
    "barclays",
    "hsbc",
    "santander",
    "lloyds",
    "royal bank of scotland",
    "rbs",
    "american express",
    "amex",
    "mastercard",
    "visa",
    "discover",
    
    # Logistics & Delivery
    "dhl",
    "fedex",
    "ups",
    "usps",
    "royal mail",
    "dpd",
    "hermes",
    "evri",
    
    # Government & Tax Authorities
    "irs",
    "internal revenue service",
    "hmrc",
    "hm revenue & customs",
    "social security administration",
    "treasury",
]

# ---------------------------------------------------------------------------
# 2. Allowed Simulated Domain Suffixes & Patterns
# ---------------------------------------------------------------------------

ALLOWED_SIMULATED_DOMAIN_SUFFIXES: list[str] = [
    ".example-corp-sim.local",
    ".sim-training.test",
    ".corp-sim.local",
    ".sim.local",
    ".sim-training.test",
    ".test",
    ".example",
    ".invalid",
    ".local",
]

# Regex to validate a domain or host name as strictly adhering to synthetic training / RFC 2606 patterns.
ALLOWED_DOMAIN_REGEX: re.Pattern = re.compile(
    r"^[a-zA-Z0-9_-]+(?:\.[a-zA-Z0-9_-]+)*(?:\.example-corp-sim\.local|\.sim-training\.test|\.corp-sim\.local|\.sim\.local|-sim\.local|\.test|\.example|\.invalid|\.local)$",
    re.IGNORECASE,
)

# Placeholder link format allowed in simulations (e.g. [SIMULATED LINK: Invoice Portal])
SIMULATED_LINK_PATTERN: re.Pattern = re.compile(
    r"\[SIMULATED LINK:\s*[^\]]+\]",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# 3. PII Detection Regular Expressions
# ---------------------------------------------------------------------------

# US Social Security Number pattern (e.g. 123-45-6789 or 123 45 6789 or 9 digits)
SSN_PATTERN: re.Pattern = re.compile(
    r"\b(?!000|666|9\d{2})\d{3}[- ]?(?!00)\d{2}[- ]?(?!0000)\d{4}\b"
)

# Major Credit Card numbers (13 to 19 digits formatted with spaces/hyphens or raw digits)
CREDIT_CARD_PATTERN: re.Pattern = re.compile(
    r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|6(?:011|5[0-9][0-9])[0-9]{12}|3[47][0-9]{13}|3(?:0[0-5]|[68][0-9])[0-9]{11}|(?:2131|1800|35\d{3})\d{11}|(?:\d{4}[ -]){3}\d{4}|\d{16})\b"
)

# ---------------------------------------------------------------------------
# 4. Attachment & Executable Payload Patterns
# ---------------------------------------------------------------------------

DANGEROUS_ATTACHMENT_EXTENSIONS: list[str] = [
    ".exe",
    ".scr",
    ".bat",
    ".cmd",
    ".vbs",
    ".vbe",
    ".js",
    ".jse",
    ".wsf",
    ".wsh",
    ".ps1",
    ".xlsm",
    ".docm",
    ".pptm",
    ".iso",
    ".img",
    ".hta",
    ".cpl",
    ".jar",
    ".apk",
    ".dmg",
    ".pkg",
]

EXECUTION_ACTION_KEYWORDS: list[str] = [
    "run the attached",
    "execute the attached",
    "open the attached executable",
    "enable macros",
    "enable content to view",
    "run setup",
    "install the update",
    "double click the attached",
    "extract and run",
]
