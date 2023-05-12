import serial as pyserial
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
        self.serial = pyserial.Serial()

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
        self.serial.port = port
        self.serial.baudrate = baud
        self.serial.timeout = timeout

        if self.serial.is_open:
            self.serial.close()
        self.serial.open()
        if self.serial.is_open:
            print('-'*40)
            print('Opened serial connection')
            print('\tport: {}'.format(self.serial.port))
            print('\tdatarate: {} bps'.format(self.serial.baudrate))
            print('-'*40)
        else:
            raise Exception("Failed to {} at {}".format(port, baud))

    def write(self, opcode, data=None):
        """
        Writes a command to the Roomba.

        Args:
            opcode: See create api
            data: A tuple containing data associated with the given opcode.
        """
        cmd = (opcode,)

        if data:
            cmd += data
        self.serial.write(struct.pack("B" * len(cmd), *cmd))

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
        if self.serial.is_open:
            print("Closing port {} at {}".format(
                self.serial.port, self.serial.baudrate))
            self.serial.close()
