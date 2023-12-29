# Configuration settings.  Note the set temperature is stored separately in config.json

config = {
    # The default target temp.
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
    # Maximum allowable target temperature. Ensure you understand the risks if you
    # raise this over 104
    "maximum_temp": 104,
    # How long to show the setting temperature after pressing the up or down buttons
    "show_settings_seconds": 5,
    # a newstyle board that supports " P "
    "p_board": False,
    # Define if the board runs in "C" or "F" (C boards are not supported yet)
    "board_units": "F",
    # This is the degrees to add to the temperature probe to make it accurate
    "calibration": -1.5,
    # If this is true the temp sent is modified so the Softub board determines when it should
    # turn on or off.  If it is false, then this controller sends either 75 degrees or 106 degress
    # To tell the controller to turn on or off.  The board may still run othertimes, such as
    # when it is time for a filter run
    "softub_controlled": False,
    # If the Softub controller board is replaced with a simple relay, set this to True
    "replacement_controller": False,
    # The degrees below which the pump should turn on. Used if softub_controlled is False
    "hysteresis": 4
}
