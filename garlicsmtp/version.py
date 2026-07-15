"""

version Information
"""

from . import (
	__title__,
	__version__,
	__author__,
	__license__,
	__description__,
	)
	
def print_version():
	"""Print Project information."""
	
	print(f"{__title__}")
	print(f"Version : {__version__}")
	print(f"Author : {__author__}")
	print(f"License : {__license__}")
	print(f"Descritption{__description__}")
