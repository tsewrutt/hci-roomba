try:
    from importlib.metadata import version
except ImportError:
    from importlib_metadata import version

from .create_api import Create
from .create_serial import SerialCommandInterface
from .errors import NoConnectionError
from .packets import SensorPacketDecoder

__version__ = "1.0.0"
