# Python Plugin for reception of Wunderground formatted Weatherstation data
#
# Author: mveeten
#
# Based on https://github.com/domoticz/domoticz/blob/master/plugins/examples/BaseTemplate.py
# and https://github.com/domoticz/domoticz/blob/development/plugins/examples/HTTP%20Listener.py
# Some functions borrowed from https://github.com/ffes/domoticz-buienradar
#
"""
<plugin key="WuDirect" name="Wunderground Direct Receiver" author="mveeten" version="0.2.3" wikilink="" externallink="https://github.com/vaneeten/domoticz-wudirect">
    <description>
        <h2>WuDirect</h2><br/>
        Domoticz plugin for direct interface with Personal Weather Stations.<br/>
        Expects the PWS to send data in the Weather Underground PWS Upload Protocol.<br/>
        Provides all parsed sensordata as separate devices for control purposes,<br/>
        and a few composite devices for nicer visualisation.<br/>
        <br/>
        Configuration options:
    </description>
    <params>
        <param field="Port" label="Port" width="30px" required="true" default="8008"/>
        <param field="Mode6" label="Debug" width="100px">
            <options>
                <option label="True" value="Debug"/>
                <option label="False" value="Normal"  default="true" />
                <option label="Logging" value="File"/>
            </options>
        </param>
    </params>
</plugin>
"""

import Domoticz
import urllib.parse as urlparse

SensorTable = {
    'humidity'        :    {
        'nr'    : 1,
        'name'  : 'Humidity Outdoor',
        'type'  : 'Custom',
        'scale' : 1.0,
        'offset': 0.0,
        'min'   : 0,
        'max'   : 100,
        'unit'  : '%'
    },
    'monthlyrainin'    :    {
        'nr'    : 2,
        'name'  : '',
        'type'  : '',
        'scale' : 1.0,
        'offset': 0.0,
        'min'   : 0,
        'max'   : 100000,
        'unit'  : ''
    },
    'solarradiation':    {
        'nr'    : 3,
        'name'  : 'Solar',
        'type'  : 'Solar Radiation',
        'scale' : 1.0,
        'offset': 0.0,
        'min'   : 0,
        'max'   : 1380,
        'unit'  : 'W/m^2'
    },
    'rtfreq'        :    {
        'nr'    : 4,
        'name'  : '',
        'type'  : '',
        'scale' : 1.0,
        'offset': 0.0,
        'min'   : -100,
        'max'   : 100,
        'unit'  : ''
    },
    'dewptf'        :    {
        'nr'    : 5,
        'name'  : 'Dewpoint',
        'type'  : 'Temperature',
        'scale' : 1.0/1.8,  # Farhrenheit to Celsius
        'offset': -32.0/1.8,
        'min'   : -100,
        'max'   : 100,
        'unit'  : 'C'
    },
    'baromin'    :    {
        'nr'    : 6,
        'name'  : 'Pressure',
        'type'  : 'Pressure',
        'scale' : 33.86,    # Inches Mg to hPa
        'offset': 0.0,
        'min'   : 800,
        'max'   : 1040,
        'unit'  : 'hPa'
    },
    'tempf'        :    {
        'nr'    : 7,
        'name'  : 'Temperature Outdoor',
        'type'  : 'Temperature',
        'scale' : 1.0/1.8,
        'offset': -32.0/1.8,
        'min'   : -100,
        'max'   : 100,
        'unit'  : 'C'
    },
    'windspeedmph':    {
        'nr'    : 8,
        'name'  : 'Wind Speed',
        'type'  : 'Custom',
        'scale' : 1.609344,     # mph to km/h
        'offset': 0.0,
        'min'   : 0,
        'max'   : 400,
        'unit'  : 'km/h'
    },
    'windchillf':    {
        'nr'    : 9,
        'name'  : 'Wind Chill',
        'type'  : 'Temperature',
        'scale' : 1.0/1.8,
        'offset': -32.0/1.8,
        'min'   : -100,
        'max'   : 100,
        'unit'  : 'C'
    },
    'indoorhumidity':    {
        'nr'    : 10,
        'name'  : 'Humidity Indoor',
        'type'  : 'Custom',
        'scale' : 1.0,
        'offset': 0.0,
        'min'   : 0,
        'max'   : 100,
        'unit'  : '%'
    },
    'rainin'        :    {
        'nr'    : 11,
        'name'  : 'Rain Rate',
        'type'  : 'Custom',
        'scale' : 25.4,  # inch to mm
        'offset': 0.0,
        'min'   : 0,
        'max'   : 1000,
        'unit'  : 'mm/h'
    },
    'ID'        :    {
        'nr'    : 12,
        'name'  : '',
        'type'  : '',
        'scale' : 1.0,
        'offset': 0.0,
        'min'   : '',
        'max'   : '',
        'unit'  : ''
    },
    'dateutc'   :    {
        'nr'    : 13,
        'name'  : '',
        'type'  : '',
        'scale' : 1.0,
        'offset': 0.0,
        'min'   : '',
        'max'   : '',
        'unit'  : ''
    },
    'UV'        :    {
        'nr'    : 14,
        'name'  : '$UV',
        'type'  : 'Custom',
        'scale' : 1.0,
        'offset': 0.0,
        'min'   : 0,
        'max'   : 50,
        'unit'  : ''
    },
    'indoortempf':    {
        'nr'    : 15,
        'name'  : 'Temperature Indoor',
        'type'  : 'Temperature',
        'scale' : 1.0/1.8,
        'offset': -32.0/1.8,
        'min'   : -100,
        'max'   : 100,
        'unit'  : 'C'
    },
    'winddir'   :    {
        'nr'    : 16,
        'name'  : 'Wind Direction',
        'type'  : 'Custom',
        'scale' : 1.0,
        'offset': 0.0,
        'min'   : -360,
        'max'   : 360,
        'unit'  : 'Deg'
    },
    'absbaromin':    {
        'nr'    : 17,
        'name'  : '',
        'type'  : 'Pressure',
        'scale' : 33.86,    # Inches Mg to hPa
        'offset': 0.0,
        'min'   : 800,
        'max'   : 1040,
        'unit'  : ''
    },
    'windgustmph':    {
        'nr'    : 18,
        'name'  : 'Wind Gust',
        'type'  : 'Custom',
        'scale' : 1.609344,     # mph to km/h
        'offset': 0.0,
        'min'   : 0,
        'max'   : 400,
        'unit'  : 'km/h'
    },
    'dailyrainin':    {
        'nr'    : 19,
        'name'  : 'Rain Daily',
        'type'  : 'Custom',
        'scale' : 25.4,  # inch to mm
        'offset': 0.0,
        'min'   : 0,
        'max'   : 10000,
        'unit'  : 'mm'
    }
}

CompositeSensors = {
    'THB'       : {
        'nr'    : 100,
        'type'  : "Temp+Hum+Baro",
        'src'   : ['tempf','humidity','_humstat,humidity,tempf','baromin','_forecast,baromin']
    },
    'WTC'       : {
        'nr'    : 101,
        'type'  : "Wind+Temp+Chill",
        'src'   :['winddir','_winddir,winddir','_windms10,windspeedmph','_windms10,windgustmph','tempf','windchillf']
    },
    'Barometer' : {
        'nr'    : 102,
        'type'  : "Barometer",
        'src'   : ['baromin','_forecast,baromin']
    },
    'Rain'      : {
        'nr'    : 103,
        'type'  : "Rain",
        'src'   : ['_rain100,rainin','dailyrainin']
    },
    'UV'        : {
        'nr'    : 104,
        'type'  : "UV",
        'src':  ['UV','tempf']
    }
}
    
class BasePlugin:
    enabled = False
    httpServerConn = None
    httpServerConns = {}
    httpClientConn = None
    heartbeats = 0
    
    def __init__(self):
        return
        self.Data = {}

    def onStart(self):
        if Parameters["Mode6"] != "Normal":
            Domoticz.Debugging(1)
            DumpConfigToLog()
        
        for idx,device in SensorTable.items():
            if device["name"] != "":
                if device["nr"] not in Devices:
                    if (device["type"] == "Custom"):
                        Domoticz.Device(Name=device["name"], Unit=device["nr"], TypeName=device["type"], Used=1, Options = { "Custom" : "1;%s" % (device["unit"])}).Create()
                    else:
                        Domoticz.Device(Name=device["name"], Unit=device["nr"], TypeName=device["type"], Used=1).Create()
        
        for key,device in CompositeSensors.items():
            if device["nr"] not in Devices:
                Domoticz.Device(Name=key, Unit=device["nr"], TypeName=device["type"], Used=1).Create();
        
        self.httpServerConn = Domoticz.Connection(Name="Server Connection", Transport="TCP/IP", Protocol="HTTP", Port=Parameters["Port"])
        self.httpServerConn.Listen()
        Domoticz.Log("onStart called")

    def onStop(self):
        Domoticz.Log("onStop called")

    def onConnect(self, Connection, Status, Description):
        if (Status == 0):
            Domoticz.Log("Connected successfully to: "+Connection.Address+":"+Connection.Port)
        else:
            Domoticz.Log("Failed to connect ("+str(Status)+") to: "+Connection.Address+":"+Connection.Port+" with error: "+Description)
        if (Connection != self.httpClientConn):
            self.httpServerConns[Connection.Name] = Connection
        Domoticz.Log("onConnect called")

    def onMessage(self, Connection, Data):
        Domoticz.Log("onMessage called for connection: "+Connection.Address+":"+Connection.Port)
        if Parameters["Mode6"] != "Normal":
            Domoticz.Log("URL CALLED: " + Data["URL"])
        parsed = urlparse.urlparse(Data["URL"])
        paramdict = urlparse.parse_qs(parsed.query)
        
        self.Data = {}
        
        for key,param in paramdict.items():
            value = param[0]
            if key in SensorTable:                
                device = SensorTable[key]
                
                if (device["name"] != "") :                
                    unitnr = device["nr"]
                    scale  = device["scale"]
                    offset = device["offset"]
                    minval = device["min"]
                    maxval = device["max"]
                    self.Data[key] = None
                    if Parameters["Mode6"] != "Normal":
                        Domoticz.Log("Updating sensor: %s (Scale %.3f, offset %.3f" % (str(unitnr),scale,offset))
                    try:
                        if (is_number(value)):
                            fvalue = float(value) * scale + offset
                            if (fvalue >= minval and fvalue <= maxval):
                                svalue = "%.1f" % fvalue
                                UpdateDevice(unitnr,0,svalue)
                                svalue = "%.6f" % fvalue
                                self.Data[key] = svalue
                            else:
                                Domoticz.Log("Sensor value for device %i out of range and discarded: %.1f" % (unitnr, fvalue))
                        else:
                            Domoticz.Log("Sensor value for device %i NOT numeric: %s" % (unitnr, str(value)))
                            # UpdateDevice(unitnr,0,value)
                            self.Data[key] = None
                    except:
                        Domoticz.Log("Sensor update EXCEPTION for unit %i" % unitnr)
                else:
                    if Parameters["Mode6"] != "Normal":
                        Domoticz.Log("Sensor NOT handled in code: %s" % (key))
            else:
                if Parameters["Mode6"] != "Normal":
                    Domoticz.Log("Sensor NOT found: %s" % (key))
                
        for key,device in CompositeSensors.items():
            unitnr = device["nr"]
            data_lst = []
            value = None
            for src in device["src"]:                
                if (src[0] == '_'):
                    function,paramstr = src[1:].split(',',1)
                    params = paramstr.split(',')
                    if (function == 'forecast'):
                        value = str(getBarometerForecast(parseFloatValue(self.Data[params[0]])))
                    elif (function == 'humstat'):
                        value = str (getHumidityStatus(parseFloatValue(self.Data[params[0]]),parseFloatValue(self.Data[params[1]])))
                    elif (function == 'winddir'):
                        value = getWindDirection(parseFloatValue(self.Data[params[0]]))
                    elif (function == 'rain100'):
                        value = floatToString( parseFloatValue(self.Data[params[0]]) * 100.0 )
                    elif (function == 'windms10'):
                        value = floatToString( parseFloatValue(self.Data[params[0]]) * 10.0 /3.6 )
                else:
                    value = self.Data[src]
                    if (is_number(value)):
                        fvalue = float(value)
                        value = "%.1f" % fvalue
                if (value !=  None and type(value) == str):
                    data_lst.append( value )

            if len(data_lst) == len(src):   # exactly right amount of values?
                svalue = ';'.join(data_lst)
                UpdateDevice(unitnr,0,svalue)
        
        # EXAMPLE URL:
        # /weatherstation/updateweatherstation.php?ID=IXXXXXX&PASSWORD=NoKeyNeeded&indoortempf=72.9&tempf=66.9&dewptf=63.0&windchillf=66.9&indoorhumidity=65&humidity=87&windspeedmph=1.6&windgustmph=2.2&winddir=196&absbaromin=29.740&baromin=29.918&rainin=0.000&dailyrainin=0.059&weeklyrainin=1.220&monthlyrainin=1.500&solarradiation=86.73&UV=0&dateutc=2019-08-17%2012:42:23&softwaretype=EasyWeatherV1.4.1&action=updateraw&realtime=1&rtfreq=5
        
        # Incoming Requests
        if "Verb" in Data:
            strVerb = Data["Verb"]
            LogMessage(strVerb+" request received.")
            data = "<!doctype html><html><head></head><body><h1>Successful GET!!!</h1></body></html>"
            if (strVerb == "GET"):
                Connection.Send({"Status":"200 OK", "Headers": {"Connection": "keep-alive", "Accept": "Content-Type: text/html; charset=UTF-8"}, "Data": data})
            elif (strVerb == "POST"):
                Connection.Send({"Status":"200 OK", "Headers": {"Connection": "keep-alive", "Accept": "Content-Type: text/html; charset=UTF-8"}, "Data": data})
            else:
                Domoticz.Error("Unknown verb in request: "+strVerb)    
        Domoticz.Log("onMessage called")

    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Log("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Log("Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self, Connection):
        if Connection.Name in self.httpServerConns:
            del self.httpServerConns[Connection.Name]    
        Domoticz.Log("onDisconnect called")

    def onHeartbeat(self):
        if (self.httpClientConn == None or self.httpClientConn.Connected() != True):
            self.httpClientConn = Domoticz.Connection(Name="Client Connection", Transport="TCP/IP", Protocol="HTTP", Address="127.0.0.1", Port=Parameters["Port"])
            self.httpClientConn.Connect()
            self.heartbeats = 0

        self.heartbeats += 1    
        # Domoticz.Log("onHeartbeat called")

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

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

# Generic helper functions
def LogMessage(Message):
    if Parameters["Mode6"] != "Normal":
        Domoticz.Log(Message)
    elif Parameters["Mode6"] != "Debug":
        Domoticz.Debug(Message)
    else:
        f = open("http.html","w")
        f.write(Message)
        f.close()   

def DumpConfigToLog():
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
    
# Update Device into database
def UpdateDevice(Unit, nValue, sValue, AlwaysUpdate=False):
    # Make sure that the Domoticz device still exists (they can be deleted) before updating it
    if Unit in Devices:
        if Devices[Unit].nValue != nValue or Devices[Unit].sValue != sValue or AlwaysUpdate == True:
            Devices[Unit].Update(nValue, str(sValue))
            # Domoticz.Log("Update " + Devices[Unit].Name + ": " + str(nValue) + " - '" + str(sValue) + "'")
    return

def is_number(s):
    try:
        float(s)
        return True
    except:
        pass
    return False

# From: buienradar.py
#
# Based on https://nl.wikipedia.org/wiki/Gevoelstemperatuur
#
def getWindChill(temperature,windSpeed):

    # Do we have a temperature?
    if temperature == None:
        return None

    # Wind chill is only valid for temperatures between -46 C and +10 C
    if temperature < -46 or temperature > 10:
        return temperature

    # No wind, no wind chill
    if windSpeed == None:
        return temperature

    # Wind chill is only valid for wind speed between 1.3 m/s and 49 m/s
    if windSpeed < 1.3 or windSpeed > 49:
        return temperature

    # Calculate the wind chill based on the JAG/TI-method
    if temperature != None and windSpeed != None:
        windChill = round(13.12 + (0.6215 * temperature) - (13.96 * pow(windSpeed, 0.16)) + (0.4867 * temperature * pow(windSpeed, 0.16)), 1)
    else:
        windChill = None
    return windChill


# From: buienradar.py
#
# Convert the wind direction to a (English) abbreviation
#

def getWindDirection(windBearing):

    if windBearing == None:
        return ""

    if windBearing < 0 or windBearing > 360:
        return ""

    if windBearing > 348 or  windBearing <=  11:
        return "N"
    if windBearing >  11 and windBearing <=  33:
        return "NNE"
    if windBearing >  33 and windBearing <=  57:
        return "NE"
    if windBearing >  57 and windBearing <=  78:
        return "ENE"
    if windBearing >  78 and windBearing <= 102:
        return "E"
    if windBearing > 102 and windBearing <= 123:
        return "ESE"
    if windBearing > 123 and windBearing <= 157:
        return "SE"
    if windBearing > 157 and windBearing <= 168:
        return "SSE"
    if windBearing > 168 and windBearing <= 192:
        return "S"
    if windBearing > 192 and windBearing <= 213:
        return "SSW"
    if windBearing > 213 and windBearing <= 237:
        return "SW"
    if windBearing > 237 and windBearing <= 258:
        return "WSW"
    if windBearing > 258 and windBearing <= 282:
        return "W"
    if windBearing > 282 and windBearing <= 303:
        return "WNW"
    if windBearing > 303 and windBearing <= 327:
        return "NW"
    if windBearing > 327 and windBearing <= 348:
        return "NNW"

    # just in case
    return ""


# From: buienradar.py
# Based on various pictures of analogue barometers found in the Internet
#
def getBarometerForecast(pressure):

    if pressure == None:
        return 5

    # Thunderstorm = 4
    if pressure < 966:
        return 4

    # Cloudy/Rain = 6
    if pressure < 993:
        return 6

    # Cloudy = 2
    if pressure < 1007:
        return 2

    # Unstable = 3
    if pressure < 1013:
        return 3

    # Stable = 0
    if pressure < 1033:
        return 0

    # Sunny = 1
    return 1


# From: buienradar.py
# Based on Mollier diagram and Fanger (comfortable)
# These values are normally used for indoor situation,
# but this weather lookup plugin obviously is outdoor.
#
def getHumidityStatus(humidity,temperature):

    # Is there a humidity?
    if humidity == None:
        return 0

    # Dry?
    if humidity <= 30:
        return 2

    # Wet?
    if humidity >= 70:
        return 3

    # Comfortable?
    if humidity >= 35 and humidity <= 65:
        if temperature != None:
            if temperature >= 22 and temperature <= 26:
                return 1

    # Normal
    return 0

    
#
# Parse an int and return None if no int is given
#    
def parseIntValue(s):
    try:
        return int(s)
    except:
        return None

#
# Parse a float and return None if no float is given
#
def parseFloatValue(s):
    try:
        return float(s)
    except:
        return None

#
# Format a float to a string and return empty string if no valid float is given
#
def floatToString(fval):
    if fval == None:
        return ""
    retval = ""
    try:
        retval = "%.1f" % fval
    except:
        retval = ""
    return retval 
