# micropython-esp32
Mein DIY Projekt für den Einsatz eines esp32 mit micropython.\
![Display_Sensors](https://user-images.githubusercontent.com/91437265/144920786-8a60ea24-bfb9-463e-80cc-e4714e166f22.jpg)

## Inhalt
Das Projekt besteht zum einem aus den Kernmodulen, mit dennen der esp32 initialisiert wird.
Zum Anderen Teil beinhaltet das Projekt die Applikation für die vorgesehenen Aufgaben des Mikrocontrollers.

### Core

* Boot:		Initialisierung des Setup bei fehlender Boot-Konfiguration
* Setup:	Funktion zum Laden und Speichern der Konfigurationsparameter
* Main:		Startroutine zur Initialisierung der esp-Funktionen mittels Boot- oder Default-Konfiguration:

#### Startroutine

* SD-Card einbinden
* WiFi-Verbindung herstellen
* Access Point starten
* RTC Zeitsynchronisierung mit UTC
* RTC Modul No-WiFi Fallback
* Status der esp-Funktionen speichern

### App
<details><summary>Show more</summary>


* Sensoren:		Klasse zur Initialisierung von Sensoren mit I2C, UART
* Scoring:		Klasse zur Auswertung der Sensoren-Messwerte
* Display:  	Klasse zur Verwendung des SPI-Display Treiber ILI9341
* Lightstrip: 	Klasse zur Verwendung von Neopixel
* Applikation:	Funktionsablauf der Anwendung

	#### Initialisierung
	* Konfiguration:	Laden der Applikations-Konfiguration		
	* Sensoren:			Initialisierung und Steuerung der Sensoren mittels Konfigurationsparameter		
	* Lightstrip:		Initialisierung des Lightstrip mittels Konfigurationsparameter		
	* Display:			Initialisierung und Steuerung des Display mittels Konfigurationsparameter
	
	#### Schleifen
	* Speichern der Sensoren-Meßwerte
	* Prüfen und Wiederherstellen der WiFi-Verbindung
	* Displayausgabe der Uhrzeit, Verbindungsstatus, Sensoren-Messwerte und Warnungen
	* TODO: Speichern der Sensoren-Messwerte in einer CSV-Datei
	
	#### Features
	* Leuchtstreifen bei Überschreitung von Sensor-Schwellwerten ansteuern
	* Ausgabe von min. und max. Werten für Temperatur, CO2
	* Ausgabe der Differenz zum letzten Messwert
	* Zeitgesteuertes Zurücksetzen der min. und max. Werte
</details>	

## Getting Started

### Tools

### Micropython

## Core
Wir der esp32 gestartet werden die Skripte boot.py und main.py ausgeführt.

Das Laden der Konfigurationsdateien und Speichern der Parameter ist in der boot.py ausgelagert.\
Im Skript main.py werden die esp-Funktionen mittels Konfigurationsparameter initialisiert.


### Filesystem
```
├── core
│   ├── wifi.py
│   ├── database.py
│   ├── sdcard.py
│   └── timezone.py
├── config
│   ├── boot.json
│   └── network.json
├── boot.py
├── main.py
└── setup.py
```

### Boot
In der ```boot.py``` wird geprüft, ob die Datei boot.db existiert.\
Existiert die Datei nicht wird das Setup ausgeführt, über welches alle Konfigurationsdateien erneut geladen werden.

### Setup
In der ```setup.py``` werden die Konfigurationsdateien eingelesen und die enthaltenen Daten in dem übergebenem binary-File überführt.\
Das Setup kann ggf. mit weiteren Konfigurationsdateien ergänzt werden.
```python
# boot config
setConfig("/boot.db", ["boot.json"])

# network config
setConfig("/network.db", ["network.json"], delete_json=False, delete_db=True)

# more configs if needed
# setConfig("/app/app.db", ["app.json", "tft.json", "sensors.json"], delete_json=False, delete_db=True)
```

#### Konfigurationsdateien

##### Boot
In der Konfigurationsdatei ```boot.json``` werden die Start-Parameter definiert, mit dennen die esp-Funktionen initialisiert werden.

```
├── config
│   └── boot.json
```
<details><summary>boot.json</summary>
<p>

	{
	    "DEBUG"   : true,
	    "TIMEZONE": {
		"UTC"     : 1,
		"ZONE"    : "MESZ - Mitteleuropäische Winterzeit (UTC+1)",
		"SUMMMER" : 3,
		"WINTER"  : 10
	    },
	    "DEVICE" : {
		"TYPE"   : "ESP32-WROVER",
		"BRAND"  : "Tonysa",
		"MODEL"  : "TTGO T8 V1.7.1",
		"PSRAM"  : "8MB",
		"FLASH"  : "4MB",
		"SDCARD" : "Mount on SPI Slot 1",
		"SDSLOT" : "Slot 1 mosi=15, sck=14, dat1=4, dat2=12",
		"SDPINS" : "Pins cs=13, miso=2"
	    },
	    "SDCARD" : {
		"SPI"  : 1,
		"CS"   : 13,
		"MOSI" : 2,
		"PATH" : "/sd"
	    },
	    "RTC" : {
		"MODUL" : "DS1307"
	    },
	    "NETWORK" : {
		"RECONNECT" : 7200,
		"DATABASE"  : "/network.db",
		"DEFAULT"   : "default",
		"WIFI"      : false,
		"SMART"     : true,
		"AP_IF"     : false,
		"AP"        : false
	    },
	     "I2C" : {
		"SLOT" : 1,
		"SDA"  : 21,
		"SCL"  : 22,
		"FREQ" : 400000
	    }
	}

</p>
</details>

| Objekt     | Parameter | Typ     | Default   | Funktion                                                                              |
|------------|-----------|---------|-----------|---------------------------------------------------------------------------------------|
|            | DEBUG     | boolean | false     | Im Debug Modus werden mehr Logausgaben erzeugt                                        |
|            | BLUETOOTH | boolean | ---       | nicht implementiert                                                                   |
| TIMEZONE   |           | object  | undefined | Zeitsynchronisierung initialisieren                                                   |
| TIMEZONE   | UTC       | integer | undefined | Zeitzone zur synchronisierung des internen RTC                                        |
| TIMEZONE   | ZONE      | string  | undefined | Optional                                                                              |
| SDCARD     |           | object  | undefined | SD-Card im Filesystem einbinden                                                       |
| SDCARD     | PATH      | string  | undefined | Pfad zur SD-Card im Filesystem                                                        |
| SDCARD     | SPI       | integer | undefined | SPI Slot                                                                              |
| SDCARD     | CS        | integer | undefined | CS-Pin                                                                                |
| SDCARD     | MOSI      | integer | undefined | MOSI-Pin                                                                              |
| SDCARD     | WIDTH     | integer | undefined | selects the bus width for the SD/MMC interface.                                       |
| RTC        |           | object  | undefined | externes RTC Modul verwenden, falls keine Zeitsynchronisierung möglich                |
| RTC        | MODUL     | string  | undefined | Name des RTC Modul                                                                    |
| NETWORK    |           | object  | defined   | WiFi und/oder Access Point initialisieren                                             |
| NETWORK    | RECONNECT | integer | undefined | Interval zur WiFi Verbindungsprüfung, 0 = off (use in Application)                    |
| NETWORK    | WIFI      | boolean | false     | WiFi initialisieren                                                                   |
| NETWORK    | SMART     | boolean | undefined | Ablgeich zwischen WLAN-Scan und gespeicherten Netzwerken zur Verbindungsherstellung   |
| NETWORK    | AP_IF     | boolean | false     | Access Point als Fallback initialisieren (WiFi not connected)                         |
| NETWORK    | AP        | boolean | true      | Access Point initialisieren                                                           |

boot config is missing => default

##### Networks
In der Konfigurationsdatei ```network.json``` werden die Neztwerkverbindungen gespeichert.
```
├── config
│   └── network.json
```
<details><summary>network.json</summary>
<p>
	
	```
	{
	    "default" : {
		    "essid"     : "router",
		    "password"  : "7612536812763",
		    "static_ip" : false,
		    "ip"        : "192.168.2.1",
		    "subnet"    : "255.255.255.0",
		    "gateway"   : "192.168.2.1",
		    "dns"       : "192.168.2.1"
	     },
	     "WLAN-001" : {
		    "essid"     : "WLAN-001",
		    "password"  : "09128309809",
		    "static_ip" : true,
		    "ip"        : "192.168.2.1",
		    "subnet"    : "255.255.255.0",
		    "gateway"   : "192.168.2.1",
		    "dns"       : "192.168.2.1"
	      },
	     "Hotspot" : {
		    "essid"     : "Hotspot",
		    "password"  : "9812739812"
	      }
	}
	```
</p>
</details>

##### NETWORK
Zur Verwendung der Neztwerfunktionen müssen im Objekt ```NETWORK=true``` nachfolgende Parameter verwendet werden.


#### WIFI
Zur Initialisierung einer drahtlosen Neztwerkverbindung muss der Parameter ```WIFI=true``` im Objekt ```NETWORK``` gesetzt sein.
##### SMART
Ist der Parameter ```SMART=true``` zusätzlich gesetzt, werden die gespeicherten Netzwerke mit den WLAN-Scan des esp32 abgeglichen und im ersten Trefferfall eine Verbindung hergestellt.\
Wird die WiFi-Verbindung nicht ```SMART=false``` initialisiert, muss eine ```default``` Neztwerkverbindung in der Konfigurationsdatei ```network.json```definiert sein.

#### Access Point

##### AP
Zur Initialisierung des Access Point muss der Parameter ```AP=true``` gesetzt sein.

##### AP_IF
Der Access Point wird mittels Parameter ```AP_IF=true``` als Fallback initialisiert, wenn eine drahtlose Neztwerkverbindung nicht hergestellt werden konnte.

### Main

### Module

