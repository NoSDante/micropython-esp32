# micropython-esp32
Mein DIY Projekt für den Einsatz eines esp32 mit micropython.

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
In der boot.py wird geprüft, ob die Datei boot.db existiert.\
Existiert die Datei nicht wird das Setup ausgeführt, über welches alle Konfigurationsdateien erneut geladen werden.

### Setup
In der setup.py werden die Konfigurationsdateien eingelesen und die enthaltenen Daten in dem übergebenem binary-File überführt.\
Das Setup kann ggf. mit weiteren Konfigurationsdateien ergänzt werden.
```
# boot config
setConfig("/boot.db", ["boot.json"])

# network config
setConfig("/network.db", ["network.json"], delete_json=False, delete_db=True)

# more configs if needed
# setConfig("/app/app.db", ["app.json", "tft.json", "sensors.json"], delete_json=False, delete_db=True)
```

#### Konfigurationsdateien

##### Boot
In der Datei ```boot.json``` werden die Konfigurationsdateien definiert, mit dennen die esp-Funktionen initialisiert werden.

```
├── config
│   └── boot.json
```
| Objekt     | Parameter | Typ     | Default   | Funktion                                                                              |
|------------|-----------|---------|-----------|---------------------------------------------------------------------------------------|
| BOOT       | DEBUG     | boolean | false     | Im Debug Modus werden mehr Logausgaben erzeugt                                        |
| BOOT       | BLUETOOTH | boolean | false     | nicht implementiert                                                                   |
| BOOT       | SDCARD    | boolean | false     | SD-Card im Filesystem einbinden (Parameter im Objekt SCDCARD erforderlich)            |
| BOOT       | NETWORK   | boolean | true      | WiFi und/oder Access Point initialisieren (Parameter im Objekt NETWORK erforderlich)  |
| TIMEZONE   | UTC       | integer | undefined | Zeitzone zur synchronisierung des internen RTC                                        |
| TIMEZONE   | ZONE      | string  | undefined | Optional                                                                              |
| SDCARD     | PATH      | string  | undefined | Pfad zur SD-Card im Filesystem                                                        |
| SDCARD     | SPI       | integer | undefined | SPI Slot (optional)                                                                   |
| SDCARD     | CS        | integer | undefined | CS-Pin   (optional)                                                                   |
| SDCARD     | MOSI      | integer | undefined | MOSI-Pin (optional)                                                                   |
| RTC        | INIT      | boolean | undefined | externes RTC Modul verwenden, falls keine Zeitsynchronisierung möglich                |
| RTC        | MODUL     | string  | undefined | Beschreibung des RTC (optional)                                                       |
| NETWORK    | RECONNECT | integer | undefined | Interval zur WiFi Verbindungsprüfung, 0 = off                                         |
| NETWORK    | WIFI      | boolean | false     | WiFi initialisieren                                                                   |
| NETWORK    | SMART     | boolean | undefined | Ablgeich zwischen WLAN-Scan und gespeicherten Netzwerken zur Verbindungsherstellung   |
| NETWORK    | AP_IF     | boolean | false     | Access Point als Fallback initialisieren (WiFi not connected)                         |
| NETWORK    | AP        | boolean | true      | Access Point initialisieren                                                           |

##### Network
In der Datei ```network.json``` werden die Neztwerkverbindungen gespeichert.
Zur Verwendung der Neztwerfunktionen muss der Parameter ```NETWORK=true``` gesetzt sein.
```
├── config
│   └── network.json
```

<details>
  <summary>network.json</summary>
<p>
```yaml
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
</p>
</details>


#### WiFi
Zur Initialisierung einer drahtlosen Neztwerkverbindungen muss der Parameter ```WIFI=true``` gesetzt sein.
Ist der Parameter ```SMART=true``` gesetzt, werden die gespeicherten Netzwerke mit den WLAN-Scan des esp32 abgeglichen und im ersten Trefferfall eine Verbindung hergestellt.\
Wird die WiFi-Verbindung nicht ```SMART``` initialisiert, muss im Objekt "default" ein Standardnetzwerk definiert sein.

#### Access Point





### Main

### Module

