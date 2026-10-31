"""FileTools — Converter package."""
__version__ = "0.1.0"
__all__ = ["convert_file", "convert_directory", "SUPPORTED_CONVERSIONS"]

from converter.core import convert_file, convert_directory, SUPPORTED_CONVERSIONS
