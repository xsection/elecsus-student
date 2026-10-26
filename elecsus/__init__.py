from importlib.metadata import PackageNotFoundError, version as _version

try:
    __version__ = _version('ElecSus')
except PackageNotFoundError:   # run from a source tree that was never installed
    __version__ = '0+unknown'
