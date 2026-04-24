import os
import pytest
from dotenv import load_dotenv

# Load .env before importing auth (so JWT_SECRET is set)
load_dotenv()

# Set a test-safe JWT_SECRET if not already set
if not os.getenv("JWT_SECRET"):
    os.environ["JWT_SECRET"] = "test-secret-key"
