"""
FormoG2P - 台灣本土語言 G2P 工具

支援語言:
- 客語 (Hakka): from formog2p.hakka import g2p
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("formog2p")
except PackageNotFoundError:
    __version__ = "0.0.0.dev"

__all__ = ["__version__"]
