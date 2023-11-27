import busio
import supervisor
from ticks import calc_due_ticks_ms, calc_due_ticks_sec, is_due
from log import log


class Softub:
    # After the up or down arrows is pressed to change the temperature, show the
    # set temp for this long
    show_setting_seconds = 8
    # The amount of time to show "P" instead of the actual temp.  Stock is 2 minutes
    # I think its better to use 0, even though it will show low temps.
    p_setting_seconds = 2 * 60
    # The last set temparature returned by board
    board_led_temp = 102
    # The temperature to report to the top unit
    top_led_temp = 0
    # Sent by newer boards for when pump isn't running.
    board_p = False
    # How often the status should be updated
    polling_ms = 333
    button_ms = 200
    debug_buttons = None
    debug_board = str(board_led_temp)
    display_callback = None
    # If true, it will display temps in .1 increments, without the hundreds value
    display_tenths = True

    # A copy of the LED's on the top unit
    display_buffer = bytearray([0x02, 0x00, 0x01, 0x00, 0x00, 0x01, 0xFF])
    # A copy of the last update from the board
    board_buffer = bytearray([0x02, 0x00, 0x01, 0x00, 0x00, 0x01, 0xFF])

    # the buttons currently pressed on the top unit, and the time of press
    top_buttons = 0
    top_buttons_ms = 0

    # The buttons currently being sent to board
    button_state = 0
    button_timeout = 0

    # If this is non-zero it indicates that the temperature returned is the set temp
    end_show_setting_seconds = 0

    button_jets = 0x01
    button_light = 0x02
    button_up = 0x04
    button_down = 0x08
    last_tick = 0

    def __init__(self, board_tx, board_rx, top_tx, top_rx, display_callback=None, display_tenths=True):
        self.uart_board = busio.UART(
            board_tx, board_rx, baudrate=2400, receiver_buffer_size=13
        )
        self.uart_top = busio.UART(
            top_tx, top_rx, baudrate=2400, receiver_buffer_size=1
        )
        self.due = calc_due_ticks_sec(0)
        self.display_callback = display_callback
        self.display_tenths = display_tenths

    ###
    #  Methods to read state from Softub
    ###

    # Reads any button presses from the top unit
    def read_buttons(self):
        if is_due(self.end_show_setting_seconds):
            self.end_show_setting_seconds = 0
        while self.uart_top.in_waiting:
            while self.uart_top.in_waiting:
                raw = self.uart_top.read(1)[0]
            # The 4 button bits are replicated and inverted between the
            # low and high nybbles
            # Check that they match, and extract just one copy.
            if (raw & 0x0F) == (((raw >> 4) & 0x0F) ^ 0x0F):
                new_buttons = raw >> 4
                if new_buttons != self.top_buttons:
                    self.top_buttons = new_buttons
                    self.top_buttons_ms = supervisor.ticks_ms()
            else:
                log("Received invalid button: "+str(raw))
                return
            if new_buttons:
                log("button", new_buttons)
            if self.top_buttons and (self.button_up | self.button_down):
                # If up or down arrows were pressed, show set temp
                self.end_show_setting_seconds = calc_due_ticks_sec(
                    self.show_setting_seconds - 0.5
                )

    # Updates from the board to the LED
    def read_board(self):
        while self.uart_board.in_waiting > 6:
            # If we are behind, catch up
            while self.uart_board.in_waiting > 6:
                raw = self.uart_board.read(7)
            while raw[0] != 0x02 or raw[6] != 0xFF:
                byte = self.uart_board.read(1)
                # timeout, so bail
                if not byte:
                    return
                raw = bytearray(raw[1:])
                raw.extend(byte)
                raw = list(raw)
            sum = 0
            self.display_p = False
            for i in range(1, 5):
                sum += raw[i]
                self.display_p |= raw[i] == 11
            if (sum & 0xFF) != raw[5]:
                log(
                    "invalid checksum "
                    + str(sum & 0xFF)
                    + " "
                    + str(raw[5])
                    + " "
                    + str(raw[0])
                )
                return
            if True:  # not self.display_p and self.end_show_setting_seconds:
                # log(" ".join("%02x" % b for b in raw))
                self.board_led_temp = (
                    (raw[2] % 10) * 100 + (raw[3] % 10) * 10 + (raw[4] % 10)
                )
            self.board_buffer = raw
            self.debug_board = (
                str(self.board_led_temp)
                + " "
                + str(raw[1])
                + " "
                + str(self.top_buttons)
            )
            # log(self.debug_board)

    def get_digit(self, c):
        return '0123456789 P'[self.board_buffer[c]]

    def get_display(self):
        return self.get_digit(2) + self.get_digit(3) + self.get_digit(4)

    def is_heat(self):
        return self.board_buffer[1] & 0x20

    def is_filter(self):
        return self.board_buffer[1] & 0x10

    def get_temp(self):
        return self.board_led_temp

    ###
    # Methods to send updates to Softub
    ###

    # Methods to board
    def click_button(self, button):
        if not button:
            raise Exception("No button")
        self.button_state = button
        self.button_timeout = calc_due_ticks_ms(self.button_ms)

    def display_temperature(self, tempF):
        if self.display_tenths:
            temp = int(round(tempF * 10))
            if temp >= 1000:
                if temp % 10:
                    temp = temp % 1000
                else:
                    temp = temp // 10
            h = temp // 100
        else:
            temp = int(round(tempF))
            # 0A is blank
            h = 0x0A if temp < 100 else temp // 100
        self.display_set_digits(h, int((temp // 10) % 10), int(temp % 10))

    # Values in digit places:
    # 0 - 9 - digit
    # 0x0a - blank
    # 0x0b -- "P"
    def display_set_digit(self, digit: int, value: int):
        self.display_buffer[2 + digit] = value

    def display_set_digits(self, a: int, b: int, c: int):
        self.display_set_digit(0, a)
        self.display_set_digit(1, b)
        self.display_set_digit(2, c)

    def display_set_bits(self, byte, mask, value):
        if value:
            if (self.display_buffer[byte] & mask) == 0:
                self.display_buffer[byte] |= mask
        else:
            if (self.display_buffer[byte] & mask) != 0:
                self.display_buffer[byte] &= ~mask

    def display_filter(self, on):
        self.display_set_bits(1, 0x10, on)

    def display_heat(self, on):
        self.display_set_bits(1, 0x20, on)

    # Methods to LED
    def fn_top_update(self):
        sum = 0
        for i in range(1, 5):
            sum += self.display_buffer[i]
        self.display_buffer[5] = sum & 0xFF
        self.uart_top.write(self.display_buffer)
        #log(" ".join("%02x" % b for b in self.display_buffer))

    def debug(self):
        return self.debug_board

    def fn_board_update(self):
        encoded = (self.button_state << 4) | (self.button_state ^ 0x0F)
        self.uart_board.write(bytes([encoded]))
        #log(encoded)
        if is_due(self.button_timeout):
            if self.button_state == 0:
                self.button_timeout = 0
            else:
                self.button_state = 0
                self.button_timeout = calc_due_ticks_ms(self.button_ms)

    # The callback to update. The default is to echo
    def callback(self):
        self.display_buffer = bytearray(self.board_buffer[:])
        self.button_state = self.top_buttons
        self.button_timeout = self.due

    def poll(self):
        self.read_buttons()
        self.read_board()
        if is_due(self.due):
            while is_due(self.due):
                self.due += self.polling_ms
            self.last_tick = supervisor.ticks_ms()
            if self.display_callback:
                self.display_callback()
            else:
                self.callback()
            self.fn_top_update()
            self.fn_board_update()
