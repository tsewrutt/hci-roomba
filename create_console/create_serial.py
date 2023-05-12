import struct


class SerialCommandInterface(object):
    """
    Class that handles sending commands to the Roomba.

    Writes will take in tuples and format the data to transfer to the Roomba.
    """

    def __init__(self):
        """
        Constructor.

        Creates the serial port, but does not open it. Call open() to open
        it.
        """
        self.serial = None

    def __del__(self):
        """
        Destructor.

        Closes the serial port.
        """
        self.close()

    def open(self, port, baud=115200, timeout=1):
        """
        Opens a serial port to the Roomba.

        Args:
            port: The serial port to open.
            baud: The default is 115200 but can be changed to a lower rate via the Create API.

        Raises:
            Exception: An error occurred opening the serial port.
        """
        self.port = port
        self.baudrate = baud
        print('-'*40)
        print('Opened serial connection')
        print('\tport: {}'.format(self.port))
        print('\tdatarate: {} bps'.format(self.baudrate))
        print('-'*40)

    def write(self, opcode, data=None):
        """
        Writes a command to the Roomba.

        Args:
            opcode: See Create API.
            data: A tuple containing data associated with the given opcode.
        """
        cmd = (opcode,)

        if data:
            cmd += data
        print("Writing command: {}".format(struct.pack("B" * len(cmd), *cmd)))

    def read(self, num_bytes):
        """
        Read a string of bytes from the Roomba.

        Args:
            num_bytes: The number of bytes to read.

        Returns:
            A string of bytes from the Roomba.

        Raises:
            Exception: An error occurred reading the bytes.
        """
        if not self.serial.is_open:
            raise Exception("Failed to read bytes. Serial port is not open.")

        data = self.serial.read(num_bytes)
        return data

    def close(self):
        """
        Closes the serial connection.
        """
        print("Closing port {} at {}".format(self.port, self.baudrate))
