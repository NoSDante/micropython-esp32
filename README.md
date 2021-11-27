# micropython-esp32
Mein DIY Projekt für den Einsatz eines esp32 mit micropython.

Das Projekt endet, sofern mir keine sinnvolle Aufgabe mehr für den Mikrokontroller einfällt, was erstmal nicht der Fall ist oder dieser an seine Speicherkapazitäten stößt, mal sehen.

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
	
	
## Core
Wir der esp32 gestartet werden die Skripte boot.py und main.py nacheinander ausgeführt.

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
In der boot.py wird geprüft, ob die Datei boot.db existiert.
Existiert die Datei nicht wird das Setup ausgeführt, über welches alle Konfigurationsdateien erneut geladen werden.

### Setup
In der setup.py werden die Konfigurationsdateien eingelesen und derren Parameter in einem binary-File gespeichert.
```
    # boot config
    setConfig("/boot.db", ["boot.json"])
    
    # network config
    setConfig("/network.db", ["network.json"], delete_json=False, delete_db=True)
    
    # more configs if needed
    # setConfig("/app/app.db", ["app.json", "tft.json", "sensors.json"], delete_json=False, delete_db=True)
```

### Konfigurationsdateien

#### Boot
```
boot.json
{
    "BOOT" : {
        "DEBUG"     : true
        "NETWORK"   : true
        "SDCARD"    : false
        "BLUETOOTH" : false
    },
    "TIMEZONE": {
        "UTC"     : 1
        "ZONE"    : "MESZ - Mitteleuropäische Winterzeit (UTC+1)"
    },
    "SDCARD" : {
        "SPI"  : 1
        "CS"   : 13
        "MOSI" : 2
        "PATH" : "/sd"
    },
    "RTC" : {
        "INIT"  : false
        "MODUL" : "DS1307"
    },
    "NETWORK" : {
        "RECONNECT" : 7200
        "DATABASE"  : "/network.db"
        "DEFAULT"   : "default"
        "WIFI"      : true
        "SMART"     : true
        "AP_IF"     : true
        "AP"        : false
    }
}
```

#### Network
```
network.json
{
    "default"      : {
            "essid"     : "router"
            "password"  : "7612536812763"
            "static_ip" : false
            "ip"        : "192.168.2.1"
            "subnet"    : "255.255.255.0"
            "gateway"   : "192.168.2.1"
            "dns"       : "192.168.2.1"
     },
     "WLAN-001" : {
            "essid"     : "WLAN-001"
            "password"  : "09128309809"
            "static_ip" : true
            "ip"        : "192.168.2.1"
            "subnet"    : "255.255.255.0"
            "gateway"   : "192.168.2.1"
            "dns"       : "192.168.2.1"
      },
     "Hotspot" : {
            "essid"     : "Hotspot"
            "password"  : "9812739812"
      }
}
```

### Module
