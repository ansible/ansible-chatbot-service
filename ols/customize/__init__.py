"""Contains customization packages for individual projects (for prompts/keyvords)."""

import importlib
import os

project = os.getenv("PROJECT", "ols")
prompts = importlib.import_module(f"ols.customize.{project}.prompts")
keywords = importlib.import_module(f"ols.customize.{project}.keywords")
