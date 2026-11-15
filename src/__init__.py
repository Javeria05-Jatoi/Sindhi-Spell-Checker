# Unpack the compressed data files in data/packed/ on first use (see data_files.py).
from .data_files import ensure_data as _ensure_data

_ensure_data()
