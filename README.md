Domoticz WuDirect interface for Personal Weather Stations
=========================================================

Summary
-------

This is a Domoticz Python plugin for direct reception and parsing of Wunderground-formatted Weatherstation data.  
It has been developed for the following (identical) Personal Weather Stations:  
* Fine Offset WH2900
* Alecto WS-5500 (used for development and testing)
* Ambient Weather WS-2902A

These PWS's are configured with an app "WS View" which allows sending Wunderground-formatted data to
a custom IP address. This IP address should be directed to the IP address of the Domoticz server,
and a configurable port number (default 8008).

Devices
-------

The plugin provides *separate* devices for each received data item, which are meant to be used for events.
If you set the PWS to output weather data every 60 seconds, Domoticz can respond to e.g. wind gusts 10 times quicker
than the polling rate of the Weather Underground website allows. Note that the Domoticz *logging* system has a smallest
time interval of 5 minutes, so logged trends for these devices will not have a 60 seconds resolution. Still, the event
system can handle it.

Subsequently, there are 5 *composite* devices which yield nicer plots in the Domoticz dashboard but are less
convenient when you want to trigger events.  

Installation and setup
----------------------

```bash
cd domoticz/plugins
```
or, in case you use the official Domoticz Docker image on a Synology:
Open a bash terminal to your Docker instance and type:
```bash
cd userdata/plugins  
```
or, in case you use [Jadahl's Domoticz for Synology](https://www.jadahl.com):
```bash
cd /volume1/@appstore/domoticz/var/plugins  
```
Then:

```bash
git clone https://github.com/vaneeten/domoticz-wudirect.git
```

Or (if you need elevated rights): 

```bash
sudo git clone https://github.com/vaneeten/domoticz-wudirect.git
```
Then make sure it has the execute bit set
```bash
cd domoticz-wudirect
chmod +x plugin.py
```
Finally:  

Restart your Domoticz service.

Now go to **Setup**, **Hardware** in your Domoticz interface. There you add
**Wunderground Direct Receiver**.

Please ensure that the port number matches the port number configured in WS View before starting the plugin.

Bugs and feature requests
-------------------------
Please use [GitHub Issues](https://github.com/vaneeten/domoticz-wudirect/issues)
for feature request or bug reports.

Acknowledgements
----------------

Several functions to generate data for the composite devices have been borrowed from the excellent [Buienradar plugin](https://github.com/ffes/domoticz-buienradar/) by Frank Fesevur.
I have been using his plugin for many years, until I got my own Personal Weather Station.  

And now it's time to give something back to the Domoticz community!
