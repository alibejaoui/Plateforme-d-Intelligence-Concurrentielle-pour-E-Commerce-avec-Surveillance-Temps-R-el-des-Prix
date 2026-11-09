"""
Application constants
"""

# Price availability statuses
AVAILABILITY_IN_STOCK = "in_stock"
AVAILABILITY_OUT_OF_STOCK = "out_of_stock"
AVAILABILITY_PREORDER = "preorder"
AVAILABILITY_UNKNOWN = "unknown"

# Currency codes
CURRENCY_EUR = "EUR"
CURRENCY_USD = "USD"
CURRENCY_GBP = "GBP"

# Scraping job types
JOB_TYPE_SINGLE = "single"
JOB_TYPE_BATCH = "batch"
JOB_TYPE_SCHEDULED = "scheduled"

# Default pagination
DEFAULT_PAGE_SIZE = 100
MAX_PAGE_SIZE = 1000

# Cache TTL (in seconds)
CACHE_TTL_SHORT = 60  # 1 minute
CACHE_TTL_MEDIUM = 300  # 5 minutes
CACHE_TTL_LONG = 3600  # 1 hour

