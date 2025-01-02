#!/usr/bin/env python3
import requests, time, sys
from requests.auth import HTTPBasicAuth
import logging


# Diese Daten müssen angepasst werden:
#serial = "1164a00a99df"  # Seriennummer des Hoymiles Wechselrichters
serials = []  # Seriennummern werden ausgelesen
rec_serials = False
max_power = []
rec_max_power = False
setpoint_factor = []
rec_setpoint_factor = False
maximum_wr = 3500  # Maximale Ausgabe des Wechselrichters
minimum_wr = 400  # Minimale Ausgabe des Wechselrichters

dtu_ip = '192.168.178.203'  # IP-Adresse von OpenDTU
dtu_nutzer = 'xxx'  # OpenDTU Nutzername
dtu_passwort = 'xxx'  # OpenDTU Passwort

shelly_ip = '192.168.178.93'  # IP Adresse von Shelly 3EM

grid_sum = None
power = None
altes_limit = None
reachable = None
producing = None
setpoint = None

def read_opendtu():
    global power, rec_serials, reachable, altes_limit, producing
    # Nimmt Daten von der openDTU Rest-API und übersetzt sie in ein json-Format
    r = requests.get(url=f'http://{dtu_ip}/api/livedata/status/inverters').json()

    # read_serials reading only once
    if rec_serials == False:
        # Inverter Serials for up to 10 Inverters
        for i in range(10):
            try:
                s = r['inverters'][i]['serial']  # Ist DTU erreichbar?
                serials.append(s)
                rec_serials = True
            except:
                print(f"Read {len(serials)} Inverter Serials ")
                break

    # print(serials)

    # Selektiert spezifische Daten aus der json response
    reachable = r['inverters'][0]['reachable']  # Ist DTU erreichbar?
    print("REACHABLE:")
    print(reachable)
    producing = int(r['inverters'][0]['producing'])  # Produziert der Wechselrichter etwas?
    altes_limit = int(r['inverters'][0]['limit_absolute'])  # Altes Limit
    # power_dc = r['inverters'][0]['AC']['0']['Power DC']['v'] # Lieferung DC vom Panel
    power = r['total']['Power']['v']  # Abgabe BKW AC in Watt
    print("...received opendDTU Data")
    return reachable, producing, altes_limit, power, serials, rec_serials

def read_maxpower():
    global max_power, rec_max_power
    r = requests.get(url=f'http://{dtu_ip}/api/limit/status').json()
    #print(r)
    for i in range(len(serials)):
        print(max_power)
        #max_power[i] = r[serials[i]]['max_power']
        max_power.append(r[serials[i]]['max_power'])
        rec_max_power = True
        print("MAX POWER:")
        print(max_power)
    return max_power, rec_max_power

def inv_factor():
    global max_power_all, setpoint_factor
    max_power_all = sum(max_power)
    print("asldfkjaölsdjf")
    print(max_power)
    for i in range(len(serials)):
        setpoint_factor.append(max_power[i] / max_power_all)
    rec_setpoint_factor = True
    print(f"setpoint_factor: {setpoint_factor} ")
    return max_power_all, setpoint_factor

def read_shelly():
    global grid_sum
    # Nimmt Daten von der Shelly 3EM Rest-API und übersetzt sie in ein json-Format
    phase_a = requests.get(f'http://{shelly_ip}/emeter/0', headers={'Content-Type': 'application/json'}).json()['power']
    phase_b = requests.get(f'http://{shelly_ip}/emeter/1', headers={'Content-Type': 'application/json'}).json()['power']
    phase_c = requests.get(f'http://{shelly_ip}/emeter/2', headers={'Content-Type': 'application/json'}).json()['power']
    grid_sum = phase_a + phase_b + phase_c  # Aktueller Bezug - rechnet alle Phasen zusammen
    print("...received Shelly 3EM Data")
    return grid_sum

def set_limit():
    global setpoint
    print(f'Setze Inverterlimit von {round(altes_limit, 1)} W auf {round(setpoint, 1)} W... ')
    # Neues Limit setzen
    #setpoint_each = setpoint / len(serials)
    for i in range(len(serials)):
        print(f"\nsetpoint_all: {setpoint} setpoint_each: {setpoint * setpoint_factor[i]}")
    try:
        for i in range(len(serials)):
            r = requests.post(
                url=f'http://{dtu_ip}/api/limit/config',
                data=f'data={{"serial":"{serials[i]}", "limit_type":0, "limit_value":{setpoint * setpoint_factor[i]}}}',
                auth=HTTPBasicAuth(dtu_nutzer, dtu_passwort),
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            print(f'Konfiguration gesendet ({r.json()["type"]})')
    except:
        print('Fehler beim Senden der Konfiguration')
    return setpoint



if __name__ == '__main__':
    while True:
        try:
            read_opendtu()
            # max_power reading only once
            if rec_max_power == False:
                read_maxpower()
            read_shelly()
            if rec_setpoint_factor == False:
                inv_factor()
        except:
            print('Fehler beim Abrufen der Daten')
        # Werte setzen
        print(f"Seriennummern: {serials} mit max_power: {max_power} ")
        print(f'\nBezug: {round(grid_sum, 1)} W, Produktion: {round(power, 1)} W, Verbrauch: {round(grid_sum + power, 1)} W')

        #sim
        #reachable = True
        #altes_limit = 800

        if reachable:
            setpoint = grid_sum + altes_limit - 5 # Neues Limit in Watt
            print(setpoint)

            # Fange oberes Limit ab
            if setpoint > maximum_wr:
                setpoint = maximum_wr
                print(f'Setpoint auf Maximum: {maximum_wr} W')
            # Fange unteres Limit ab
            elif setpoint < minimum_wr:
                setpoint = minimum_wr
                print(f'Setpoint auf Minimum: {minimum_wr} W')
            else:
                print(f'Setpoint berechnet: {round(grid_sum, 1)} W + {round(altes_limit, 1)} W - 5 W = {round(setpoint, 1)} W')

            if setpoint != altes_limit:
                set_limit()
                #print("test_without limit")
        else:
            print("not reachable")

        sys.stdout.flush() # write out cached messages to stdout
        time.sleep(20) # wait
