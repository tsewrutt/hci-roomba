import struct
import time
from pycreate600.errors import NoConnectionError
from pycreate600.packets import SensorPacketDecoder
from pycreate600.create_serial import SerialCommandInterface
from pycreate600.oi import OPCODES


class Create(object):
    """
    Class for controlling a Roomba.
    """

    def __init__(self, port, baud=115200):
        """
        Constructor.
        """
        self.SCI = SerialCommandInterface()
        self.SCI.open(port, baud)

        self.decoder = None

        self.sleep_timer = 1
        self.song_list = {}

    def __del__(self):
        """
        Destructor.
        """
        # stop movement
        self.drive_stop()
        time.sleep(self.sleep_timer)

        # stop motors
        self.motors_stop()
        time.sleep(self.sleep_timer)

        # turn off LEDs
        self.leds()
        time.sleep(self.sleep_timer)

    # ------------------- Mode Commands ------------------------

    def start(self):
        """
        Starts the OI.

        Changes mode to Passive. You must always send the Start command before
        sending any other commands to the OI.
        """
        try:
            self.SCI.write(OPCODES.START)
            time.sleep(self.sleep_timer)
        except Exception:
            raise NoConnectionError

    def reset(self):
        """
        Resets the robot, as if you had removed and reinserted the battery.
        """
        self.SCI.write(OPCODES.RESET)
        time.sleep(self.sleep_timer)

    def stop(self):
        """
        Stops the OI.

        All streams will stop and the Roomba will no longer respond to commands. Use
        this command when you are finished working with the Roomba.
        """
        self.clear_song_memory()
        self.SCI.write(OPCODES.STOP)
        time.sleep(self.sleep_timer)

    def safe(self):
        """
        Puts the OI into safe mode, enabling user control of Roomba.

        Turns off all LEDs. The OI can be in Passive, Safe, or Full mode to accept this
        command.
        """
        self.SCI.write(OPCODES.SAFE)
        time.sleep(self.sleep_timer)
        self.clear_song_memory()

    def full(self):
        """
        Puts the OI into full mode, giving you complete control over Roomba.
        """
        self.SCI.write(OPCODES.FULL)
        time.sleep(self.sleep_timer)
        self.clear_song_memory()

    # ------------------- Cleaning Commands ------------------------

    def clean(self):
        """
        Starts the default cleaning mode.

        This is the same as pressing Roomba's Clean button, and will pause a cleaning
        cycle if one is already in progress.
        """
        self.SCI.write(OPCODES.CLEAN)
        time.sleep(self.sleep_timer)

    def max(self):
        """
        Starts the Max cleaning mode, which will clean until the battery is dead.

        Will pause a cleaning cycle if one is already in progress.
        """
        self.SCI.write(OPCODES.MAX)
        time.sleep(self.sleep_timer)

    def spot(self):
        """
        Starts the Spot cleaning mode.

        This is the same as pressing Roomba's Spot button, and will pause a cleaning
        cycle if one is already in progress.
        """
        self.SCI.write(OPCODES.SPOT)
        time.sleep(self.sleep_timer)

    def seek_dock(self):
        """
        Directs Roomba to drive onto the dock the next time it encounters the docking
        beams.

        This is the same as pressing Roomba's Dock button, and will pause a cleaning
        cycle if one is already in progress.
        """
        self.SCI.write(OPCODES.SEEK_DOCK)
        time.sleep(self.sleep_timer)

    def power(self):
        """
        Powers down Roomba.

        The OI can be in Passive, Safe, or Full mode to accept this command.
        """
        self.SCI.write(OPCODES.POWER)
        time.sleep(self.sleep_timer)

    # ------------------- Actuator Commands ------------------------

    def drive_direct(self, r_vel, l_vel):
        """
        Lets you control the forward and backward motion of Roomba's drive wheels
        independently.

        Args:
                r_vel: Right wheel velocity (-500 - 500 mm/s)
                l_vel: Left wheel velocity (-500 - 500 mm/s)
        """
        r_vel = self._clamp(r_vel, -500, 500)
        l_vel = self._clamp(l_vel, -500, 500)
        data = struct.unpack("4B", struct.pack(">2h", r_vel, l_vel))
        self.SCI.write(OPCODES.DRIVE_DIRECT, data)

    def drive_pwm(self, r_pwm, l_pwm):
        """
        Lets you control the raw forward and backward motion of Roomba's drive wheels
        independently.

        Args:
                r_pwm: Right wheel PWM (-255 - 255)
                l_pwm: Left wheel PWM (-255 - 255)
        """
        r_pwm = self._clamp(r_pwm, -255, 255)
        l_pwm = self._clamp(l_pwm, -255, 255)
        data = struct.unpack("4B", struct.pack(">2h", r_pwm, l_pwm))
        self.SCI.write(OPCODES.DRIVE_PWM, data)

    def drive_stop(self):
        self.drive_direct(0, 0)
        time.sleep(self.sleep_timer)
    
    def motors(self, data):
        self.SCI.write(OPCODES.MOTORS, (data, ))
    
    def motors_stop(self):
        self.SCI.write(OPCODES.MOTORS, (0, ))

    def _clamp(self, value, min, max):
        """
        Clamps the given value between the given minimum and maximum values.

        Args:
                value: The value to restrict inside the range defined by the minimum
                and maximum values.
                min: The minimum value to compare against.
                max: The maximum value to compare against.

        Returns:
                The result between the minimum and maximum values.
        """
        value = value if value < max else max
        value = value if value > min else min
        return value

    # ------------------- LEDs ------------------------

    def leds(self, led_bits=0, power_colour=0, power_intensity=0):
        """
        Controls the LEDs sommon to all models of Roomba 600.

        The power LED is specified by two data bytes: one for the colour and
        the other for the intensity.

        Args:
                led_bits: [check robot, dock, spot, debris]
                power_colour: 0 = green, 255 = red. Intermediate values are
                intermediate colours (orange, yellow, etc).
                power_intensity: 0 = off, 255 = full intensity. Intermediate values are
                intermediate intensities.
        """
        data = (led_bits, power_colour, power_intensity)
        self.SCI.write(OPCODES.LEDS, data)

    # ------------------- Songs ------------------------

    def clear_song_memory(self):
        """
        Replace all songs added to the OI with a single-note 'default song'.
        """
        for i in range(4):
            song = [70, 0]
            self.song(i, song)
            self.play_song(i)
        time.sleep(self.sleep_timer)

    def song(self, song_num, notes):
        """
        Specify up to four songs to the OI that you can play at a later time.

        Each song is associated with a song number. Each song can contain up to
        sixteen notes. Each note is associated with a note number that uses MIDI
        note definitions and a duration that is specified in fractions of a second.

        Args:
                song_num (0-4): The song number associated the specific song.
                notes: 16 notes and 16 durations (1 duration = 1/64 sec)

        Returns:
                The duration of the song.

        Raises:
                Exception: An error occurred creating the song.
        """
        size = len(notes)
        if (2 > size > 32) or (size % 2 != 0):
            raise Exception(
                "Songs must be between 1-16 notes and have a duration for each note.")
        if (0 > song_num > 3):
            raise Exception("Song number must be 0-3.")

        if not isinstance(notes, tuple):
            notes = tuple(notes)

        duration = 0
        for i in range(size // 2):
            duration += notes[2 * i + 1]
        duration = duration / 64

        data = (song_num, size // 2,) + notes
        self.SCI.write(OPCODES.SONG, data)

        self.song_list[song_num] = duration

        return duration

    def play_song(self, song_num):
        """
        Play a song from the songs added to Roomba using the Song command.

        You must add one or more songs to Roomba using the Song command in
        order for the Play command to work.

        Args:
                song_num (0-4): The number of the song Roomba is to play.

        Raises:
                Exception: An error occurred playing the song.
        """
        try:
            duration = self.song_list[song_num]
        except Exception:
            print("Invalid song: {}".format(song_num))
            return 0

        self.SCI.write(OPCODES.PLAY, (song_num,))

        return duration

    # ------------------- Sensors ------------------------

    def sensors(self):
        """
        Requests the OI to send a packet of sensor data bytes.

        There are 58 different sensor data packets. Each provides a value
        of a specific sensor or group of sensors.
        """
        self.SCI.write(OPCODES.SENSORS, (100,))
        time.sleep(0.015)
        packet_byte_data = self.SCI.read(80)

        return SensorPacketDecoder(packet_byte_data)
