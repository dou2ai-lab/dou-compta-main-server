# -----------------------------------------------------------------------------
# File: __main__.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 02-12-2025
# Description: Entry point for running LLM worker as a module
# -----------------------------------------------------------------------------

"""
Entry point for LLM Worker
Allows running as: python -m services.llm_service.worker
"""

from .worker import start_worker

if __name__ == "__main__":
    start_worker()

























