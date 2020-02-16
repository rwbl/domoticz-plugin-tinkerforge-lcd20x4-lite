# Domoticz Home Automation - Plugin Tinkerforge LCD 20x4 Bricklet - Lite
# @author Robert W.B. Linn
# @version 1.0.0 (Build 20200214)
#
# NOTE: after every change restart Domoticz & check the Domoticz Log
# sudo systemctl restart domoticz.service OR sudo service domoticz.sh restart
# REFERENCES:
# Domoticz Python Plugin Development:
# https://www.domoticz.com/wiki/Developing_a_Python_plugin
# Tinkerforge LCD 20x4 Bricklet:
# Hardware:
# https://www.tinkerforge.com/en/doc/Hardware/Bricklets/LCD_20x4.html#lcd-20x4-bricklet
# API Python Documentation:
# https://www.tinkerforge.com/en/doc/Software/Bricklets/LCD20x4_Bricklet_Python.html

"""
<plugin key="tflcd20x4lite" name="Tinkerforge LCD 20x4 Bricklet - Lite" author="rwbL" version="1.0.0">
    <description>
        <h2>Tinkerforge LCD 20x4 Bricklet - Lite</h2><br/>
        The plugin enables to write characters to the LCD 20x4 display via a Domoticz text device (Type:General, SubType:Text).<br/>
        The text to be displayed is defined as a JSON formatted string (array with up-to 4 line items).<br/>
        [{"line":1,"position":n,"clear":n,"text":"Text"},{"line":2,"position":n,"clear":n,"text":"Text"},{"line":3,"position":n,"clear":n,"text":"Text"},{"line":4,"position":n,"clear":n,"text":"Text"}] <br/>
        Each line item has the key:value pairs:
        <ul style="list-style-type:square">
            <li>"line":0-3 - Integer with line index 0 to 3.</li>
            <li>"position":0-19 - Integer with position index 0 - 19.</li>
            <li>"clear":1-2 - Integer to clear the line (1) or clear the display (2) prior writing the text to the line.</li>
            <li>"Text":"Text string" - The text to be displayed.</li>
        </ul>
        Custom characters are defined in an external file and displayed via Unicode.<br/>
        When the plugin starts, the backlight is switched on, the cursor is turned off and not blinking.<br/>
        If the text of the Domoticz device is modified, the plugin connects via IP to Tinkerforge, writes the LCD line(s) as defined by the JSON string and disconnects.<br/>
        <br/>
        Note: This is the lite version of the plugin. The full version enables to use the buttons and set the configuration for the backlight and cursor.<br/>
        <br/>
        <h3>Domoticz Devices</h3>
        <ul style="list-style-type:square">
            <li>Type:General, SubType:Text, Name: JSON.</li>
        </ul>
        <br/>
        <h3>Configuration</h3>
        <ul style="list-style-type:square">
            <li>Address: IP address of the host connected to. Default: 127.0.0.1 (for USB connection)</li>
            <li>Port: Port used by the host. Default: 4223</li>
            <li>UID: Unique identifier of the LCD 20x4 Bricklet. Obtain the UID via the Brick Viewer. Default: BHN</li>
        </ul>
    </description>
    <params>
        <param field="Address" label="Host" width="200px" required="true" default="127.0.0.1"/>
        <param field="Port" label="Port" width="75px" required="true" default="4223"/>
        <param field="Mode1" label="UID" width="200px" required="true" default="BHN"/>
        <param field="Mode6" label="Debug" width="75px">
            <options>
                <option label="True" value="Debug" default="true"/>
                <option label="False" value="Normal"/>
            </options>
        </param>
    </params>
</plugin>
""" 

## Imports
import Domoticz
import urllib
import urllib.request
import json 

# Amend the import path to enable using the Tinkerforge libraries
# Alternate (ensure to update in case newer Python API bindings):
# create folder tinkerforge and copy the binding content, i.e.
# /home/pi/domoticz/plugins/tflcd20x4lite
from os import path
import sys
sys.path
sys.path.append('/usr/local/lib/python3.7/dist-packages')

import tinkerforge
from tinkerforge.ip_connection import IPConnection
from tinkerforge.bricklet_lcd_20x4 import BrickletLCD20x4

# Units
## Text lines set using JSON format - UNIT MUST start with 1
UNITJSON = 1
# Status Level & Text
STATUSLEVELOK = 1
STATUSLEVELERROR = 5
STATUSTEXTOK = "OK"
STATUSTEXTERROR = "ERROR"

# Custom Characters file JSON array format - located in the same folder as plugin.py. older name is plugin key.
CUSTOMCHARFILE = "/home/pi/domoticz/plugins/tflcd20x4lite/customchar.json"

# Messages (not all)
MSGERRNOUID = "[ERROR] Bricklet UID not set. Get the UID using the Brick Viewer."
MSGERRSETCONFIG = "[ERROR] Set bricklet configuration failed. Check bricklet and settings."

class BasePlugin:

    def __init__(self):
        self.Debug = False
        
        # NOT USED=Placeholder
        # The Domoticz heartbeat is set to every 10 seconds. Do not use a higher value than 30 as Domoticz message "Error: hardware (N) thread seems to have ended unexpectedly"
        # The plugin heartbeat is set in Parameter.Mode5 (seconds). This is determined by using a hearbeatcounter which is triggered by:
        # (self.HeartbeatCounter * self.HeartbeatInterval) % int(Parameter.Mode5) = 0
        # Example: trigger action every 60s [every 6 heartbeats] = (6 * 10) mod 60 = 0 or every 5 minutes (300s) [every 30 heartbeats] = (30 * 10) mod 300 = 0
        # self.HeartbeatInterval = 10
        # self.HeartbeatCounter = 0

    def onStart(self):
        Domoticz.Debug("onStart called")
        Domoticz.Debug("Debug Mode:" + Parameters["Mode6"])
        if Parameters["Mode6"] == "Debug":
            self.debug = True
            Domoticz.Debugging(1)
            dump_config_to_log()

        if (len(Devices) == 0):
            # Create new devices for the Hardware
            Domoticz.Debug("Creating new Device(s)")
            Domoticz.Device(Name="JSON", Unit=UNITJSON, TypeName="Text", Used=1).Create()
            Domoticz.Debug("Device created: "+Devices[UNITJSON].Name)

        # Get the UID of the bricklet
        if len(Parameters["Mode1"]) == 0:
            status_to_log(STATUSLEVELERROR, MSGERRNOUID)
            return

        # Set the bricklet configuration: backlight on,cursor on, blink on
        set_configuration(True,False,False)

    def onStop(self):
        Domoticz.Debug("Plugin is stopping.")

    def onConnect(self, Connection, Status, Description):
        Domoticz.Debug("onConnect called")

    def onMessage(self, Connection, Data):
        Domoticz.Debug("onMessage called")

    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Debug("onCommand called Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level) + "', Hue: " + str(Hue))

    # Handle new text from the text units (devices). The text is in property Devices[Unit].sValue
    def onDeviceModified(self, Unit):
        Domoticz.Debug("onDeviceModified called Unit:" + str(Unit) + " (" + Devices[Unit].Name + "),nValue="+str(Devices[Unit].nValue) + ",sValue="+Devices[Unit].sValue)
        write_lines(Unit)
        
    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Debug("Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self, Connection):
        Domoticz.Debug("onDisconnect called")

    def onHeartbeat(self):
        Domoticz.Debug("onHeartbeat called")
        # NOT USED = PLACEHOLDER
        """
        self.HeartbeatCounter = self.HeartbeatCounter + 1
        Domoticz.Debug("onHeartbeat called. Counter=" + str(self.HeartbeatCounter * self.HeartbeatInterval) + " (Heartbeat=" + Parameters["Mode5"] + ")")
        # check the heartbeatcounter against the heartbeatinterval
        if (self.HeartbeatCounter * self.HeartbeatInterval) % int(Parameters["Mode5"]) == 0:
            try:
                SetBrickletIlluminance(UNITILLUMINATION)
                return
            except:
                #Domoticz.Error("[ERROR] ...")
                return
        """

global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)

def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)

def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)

def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)

def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)

def onDeviceModified(Unit):
    global _plugin
    _plugin.onDeviceModified(Unit)

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

# Tinkerforge Bricklet

"""
Set the bricklet configuration
Parameter:
backlight - True|False = Set backlight on
cursor - True|false = set cursor on|off
blick - True|False = set blink cursor on|off
"""
def set_configuration(backlight,cursor,blinking):
    Domoticz.Debug("set_configuration")
    try:
        # Create IP connection
        ipConn = IPConnection()
        # Create device object
        lcdDev = BrickletLCD20x4(Parameters["Mode1"], ipConn)
        # Connect to brickd using Host and Port
        ipConn.connect(Parameters["Address"], int(Parameters["Port"]))
        # Update the configuration
        if backlight == True:
            lcdDev.backlight_on()
        else:
            lcdDev.backlight_off()
        lcdDev.set_config(cursor, blinking)
        
        # Set Custom Characters with index 0-7 as max 8 custom characters can be defined.
        # dzVents Lua scripts:
        # The \ character needs to be escaped, i.e. line = string.format(line, l, p, "\\u0008", domoticz.helpers.isnowhhmm(domoticz) )
        # Ensure to write in unicode \u00NN and NOT \xNN - Example: lcdDev.write_line(0, 0, "Battery: " + "\u0008")
        # JSON has no hex escape \xNN but supports unicode escape \uNNNN
        # 
        # Example custom character definition and write to the lcd:
        #     battery = [14,27,17,17,17,17,17,31] 
        #     clock = [31,17,10,4,14,31,31,0]
        #     lcdDev.set_custom_character(0, clock)
        # 
        # JSON File
        # Read the custom characters from JSON array file as defined by constant CUSTOMCHARFILE
        # JSON format examplewith 2 characters: 
        # [
        #     {"id":0,"name":"battery","char":"14,27,17,17,17,17,17,31"},
        #     {"id":1,"name":"clock","char":"31,17,10,4,14,31,31,0"}
        # ]
        # Use exception handling in case file not found
        # The id must be in range 0-7 as max 8 custom characters can be defined
        try:
            with open(CUSTOMCHARFILE) as f:
                json_char_array = json.load(f)
                Domoticz.Debug("Customchar: #characters defined: %d" % (len(json_char_array)) )
                if len(json_char_array) > 0:
                    for item in json_char_array:
                        id = int(item["id"])
                        name = item["name"]
                        char = item["char"].strip().split(",")
                        # Check if the character id is in range 0-7
                        if id >= 0 and id <= 7:
                            lcdDev.set_custom_character(id, char)
                            Domoticz.Debug("Customchar: Index=%d,Name=%s,Char=%s" % (id,name,item["char"]) )
                        else:
                            status_to_log(STATUSLEVELERROR,"Customchar: Index=%d not in range 0-7." % (id) )
                else:
                    status_to_log(STATUSLEVELERROR,"Customchar: No or wrong characters defined.")
        except:
            status_to_log(STATUSLEVELERROR,"Customchar: Can not open file=%s." % (CUSTOMCHARFILE) )
        # Disconnect
        ipConn.disconnect()
        Domoticz.Debug("set_configuration: OK")
    except:
        status_to_log(STATUSLEVELERROR, MSGERRSETCONFIG)
    return

"""
Set LCD text for the 4 lines and 20 columns using json.
Parameter:
unit - unit number as defined in the constants (see top) for the text device holding the JSON string.
The text as JSON array string [{},{}] is provided by a device unit using the property device.sValue
The JSON array has 1 to N entries with line properties.
It is possible to define an entry for a line or multiple entries for a line for different positions.
JSON keys with value explain
"line" - 0-3
"position" - 0-19
"clear": clear the display: 0=no clear,1=clear line,2=clear display
"text": text to display at the line

Example JSON string = JSON array for the 4 lines
jsonarraystring = '
[
    {"line":0,"position":0,"clear":1,"text":"TEXT 1"},
    {"line":1,"position":0,"clear":1,"text":"TEXT 2"},
    {"line":2,"position":0,"clear":1,"text":"TEXT 3"},
    {"line":3,"position":0,"clear":1,"text":"TEXT 4"}
]'
"""
def write_lines(unit):
    Domoticz.Debug("write_lines: Unit=%d,ID=%d,JSON=%s" % (unit, Devices[unit].ID, Devices[unit].sValue) )
    EMPTYLINE = "                    "
    jsonstring = Devices[unit].sValue
    if len(jsonstring) == 0:
        status_to_log(STATUSLEVELERROR,"No JSON string defined for the text device (Unit sValue empty).")
        return
    try:
        # Create IP connection
        ipConn = IPConnection()
        # Create device object
        lcdDev = BrickletLCD20x4(Parameters["Mode1"], ipConn)
        # Connect to brickd using Host and Port
        ipConn.connect(Parameters["Address"], int(Parameters["Port"]))
        # Define the lcd function write_line parameter
        line = 0
        position = 0
        text = ""
        clear = 0
        # parse the json string
        json_array = json.loads(jsonstring, encoding=None)
        Domoticz.Debug("write_lines: Lines: %d" % (len(json_array)) )
        for item in json_array:
            line = int(item["line"])
            position = int(item["position"])
            text = item["text"]
            clear = int(item["clear"])
            # Domoticz.Debug("write_lines: Items (l,p,t,c): %d,%d,%s,%d" % (line,position,text,clear) )
            # Checks
            if (line < 0 or line > 3):
                status_to_log(STATUSLEVELERROR, "write_lines: Wrong line number: %d. Ensure 0-3." % (line) )
                return
            if (position < 0 or position > 19):
                status_to_log(STATUSLEVELERROR, "write_lines: Wrong position number: %d. Ensure 0-19." % (position) )
                return
            # Clear action: 1=clear line;2=clear display
            if clear == 1:
                lcdDev.write_line(line, 0, EMPTYLINE)
            if clear == 2:
                lcdDev.clear_display()
            # Write text 
            lcdDev.write_line(line, position, text)
            status_to_log(STATUSLEVELOK, "write_lines: Line=%d,Position=%d,Text=%s" % (line,position,text) )
        # Disconnect
        ipConn.disconnect()
        Domoticz.Debug("write_lines: OK")
    except:
        status_to_log(STATUSLEVELERROR, "write_lines: Failed writing text (Unit=%d,ID=%d,JSON=%s). Check JSON definition." % (unit, Devices[unit].ID, Devices[unit].sValue) )
    return

##
# Generic helper functions
##

# Dump the plugin parameter & device information to the domoticz debug log
def dump_config_to_log():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug( "'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
    return

# Log a status message, either to the domoticz log or error
# Status level: 1=OK, 4=ERROR
def status_to_log(level,text):
    if level == STATUSLEVELOK:
        Domoticz.Log(text)
    if level == STATUSLEVELERROR:
        Domoticz.Error(text)
    return
  
# Check if a string is JSON format  
def string_is_json(myjson):
    try:
        json_object = json.loads(myjson)
    except ValueError as e:
        return False
    return True
