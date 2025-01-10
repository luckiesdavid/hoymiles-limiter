
# Nulleinspeisung bis zu 10 Hoymiles mit OpenDTU & Python Steuerung

Dies ist ein Python-Skript, das den aktuellen Hausverbrauch aus einem Shelly 3EM oder Hichi ausliest, die Nulleinspeisung berechnet und die Ausgangsleistung eines Hoymiles-Wechselrichters mit Hilfe der OpenDTU entsprechend anpasst. Somit wird kein unnötiger Strom ins Betreibernetz abgegeben.


Autostart in VM/LXC:
pv_limiter.service -> /etc/systemd/system/
sudo systemctl daemon-reload
sudo systèmctl enable pv_limiter.service
sudo systèmctl start pv_limiter.service


![diagramm](media/diagramm.jpg)

## Autoren und Anerkennung
- Dieses Skript ist ein Fork von: https://gitlab.com/p3605/hoymiles-tarnkappe
- Ein großes Lob und Dank an die OpenDTU community: https://github.com/tbnobody/OpenDTU

## Wiki
- Weitere Informationen finden Sie auf unserer Seite: https://selbstbau-pv.de/wissensbasis/nulleinspeisung-hoymiles-hm-1500-mit-opendtu-python-steuerung/
