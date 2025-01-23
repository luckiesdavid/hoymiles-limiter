
# Nulleinspeisung bis zu 10 Hoymiles mit OpenDTU & Python Steuerung

Dies ist ein Python-Skript, das den aktuellen Hausverbrauch aus einem Shelly 3EM oder Hichi ausliest, die Nulleinspeisung berechnet und die Ausgangsleistung eines Hoymiles-Wechselrichters mit Hilfe der OpenDTU entsprechend anpasst. Somit wird kein unnötiger Strom ins Betreibernetz abgegeben. Das Script liest alle in OpenDTU eingerichteten Inverter automatisch aus.

inkl. MQTT Support inkl. Homeassistant .yaml

## Install
- clone repo
- install dependencies
- pv_limiter.service -> /etc/systemd/system/
- sudo systemctl daemon-reload
- sudo systemctl enable pv_limiter.service
- sudo systemctl start pv_limiter.service


![diagramm](media/diagramm.jpg)

## Autoren und Anerkennung
- Dieses Skript ist ein Fork von: https://gitlab.com/p3605/hoymiles-tarnkappe
- Ein großes Lob und Dank an die OpenDTU community: https://github.com/tbnobody/OpenDTU
