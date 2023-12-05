# Default settings.  Note the set temperature is stored separately in config.json

config = {
    # The target temp.
    "target_temp": 102,
    # Set the displayed value to F or C for Farenheight or Celsius.
    "unit": "F",
    # how often the temperature should be checked
    "poll_seconds": 1,
    # the degree increment the + and - buttons should use on the web page
    # and softub buttons
    "increment": 0.5,
    # Minimum allowable target temperature
    "minimum_temp": 50,
    # Maximum allowable target temperature
    "maximum_temp": 106,
    "show_settings_seconds": 5,
    # a newstyle board that supports " P "
    "p_board": False,
    # Define if the board runs in "C" or "F" (C boards are not supported yet)
    "board_units": "F",
    # This is the multiplier to use when reporting temperatures when the pump is off.
    # Less than 1 it will cause less and longer cycles, greater than 1, more cycles
    # None (or 1) it is unchanged.
    "change_cycles": .5,
    # The offset to add to the measured temperature sent to the board to make it more accurate
    "calibration": -1.0,
}
