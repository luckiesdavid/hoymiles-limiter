#!/usr/bin/env python3
import requests, time, sys
from requests.auth import HTTPBasicAuth
import logging


serials = [] 
rec_serials = False
max_power = []
rec_max_power = False
setpoint_factor = []
rec_setpoint_factor = False
old_limit = []
rec_old_limit = False 
#maximum_wr = 3500  # Maximale Ausgabe des Wechselrichters
minimum_wr = 400  # Minimale Ausgabe des Wechselrichters
offset_grid = -50

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
old_limit_all = None

def read_opendtu():
    global power, rec_serials, reachable, altes_limit, producing, old_limit, old_limit_all, rec_old_limit
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
    # read old_limit only once
    if rec_old_limit == False:
        # Inverter Serials for up to 10 Inverters
        for i in range(10):
            try:
                s = r['inverters'][i]['limit_absolute']  # Ist DTU erreichbar?
                old_limit.append(s)
                rec_old_limit = True
            except:
                print(f"Read {len(old_limit)} Inverter Limits ")
                break
        old_limit_all = sum(old_limit) #sum all limits
    #print(f"Read {old_limit} Inverter Limits ")

    reachable = r['inverters'][0]['reachable']  # Ist DTU erreichbar?
    producing = int(r['inverters'][0]['producing'])  # Produziert der Wechselrichter etwas?
    altes_limit = int(r['inverters'][0]['limit_absolute'])  # Altes Limit
    # power_dc = r['inverters'][0]['AC']['0']['Power DC']['v'] # Lieferung DC vom Panel
    power = r['total']['Power']['v']  # Abgabe BKW AC in Watt
    print("...received opendDTU Data")
    return reachable, producing, altes_limit, power, serials, rec_serials

def read_maxpower():
    global max_power, rec_max_power
    r = requests.get(url=f'http://{dtu_ip}/api/limit/status').json()
    for i in range(len(serials)):
        #print(max_power)
        #max_power[i] = r[serials[i]]['max_power']
        max_power.append(r[serials[i]]['max_power'])
        rec_max_power = True

    return max_power, rec_max_power

def inv_factor():
    global max_power_all, setpoint_factor, rec_setpoint_factor
    max_power_all = sum(max_power)
    for i in range(len(serials)):
        setpoint_factor.append(max_power[i] / max_power_all)
    rec_setpoint_factor = True
    print(f"setpoint_factor: {setpoint_factor} ")
    return max_power_all, setpoint_factor

def read_shelly():
    global grid_sum
    phase_a = requests.get(f'http://{shelly_ip}/emeter/0', headers={'Content-Type': 'application/json'}).json()['power']
    phase_b = requests.get(f'http://{shelly_ip}/emeter/1', headers={'Content-Type': 'application/json'}).json()['power']
    phase_c = requests.get(f'http://{shelly_ip}/emeter/2', headers={'Content-Type': 'application/json'}).json()['power']
    grid_sum = phase_a + phase_b + phase_c 
    print("...received Shelly 3EM Data")
    return grid_sum

def set_limit():
    global setpoint
    print(f'Setze Inverterlimit von {round(altes_limit, 1)} W auf {round(setpoint, 1)} W... ')
    for i in range(len(serials)):
        print(f"setpoint_all: {setpoint} setpoint_each: {setpoint * setpoint_factor[i]}")
    try:
        for i in range(len(serials)):
            r = requests.post(
                url=f'http://{dtu_ip}/api/limit/config',
                data=f'data={{"serial":"{serials[i]}", "limit_type":0, "limit_value":{setpoint * setpoint_factor[i]}}}',
                auth=HTTPBasicAuth(dtu_nutzer, dtu_passwort),
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
           )
            print(r)
            print(f'Konfiguration gesendet ({r.json()["type"]})')
        #print(f"gesendet{setpoint * setpoint_factor[i]}:")
    except Exception as e:
        print(f'Fehler beim Senden der Konfiguration: \n {e}')
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
        except Exception as e:
            print(f'Fehler beim Abrufen der Daten {e}')

        ###### Simulation ######
        #reachable = True
        #grid_sum = 1000
        #altes_limit = 3500 #3500W = kein Limit // 0W = voll Limit
        #power = 2000

        
        # Werte setzen
        print(f"Seriennummern: {serials} mit max_power: {max_power} ")
        print(f'\nBezug: {round(grid_sum, 1)} W, Produktion: {round(power, 1)} W, altes_Limit: {round(old_limit_all, 1)} W')

        if len(max_power) & len(serials) == 4: # ATTENTION HARDCODED 4 INVERTERS!
            if reachable:

                # Export
                if grid_sum < offset_grid: 
                    setpoint = (grid_sum + power) - offset_grid# *-1

                    #  upper Limit 
                    if setpoint > max_power_all:
                        setpoint = max_power_all
                        print(f'Setpoint auf Maximum: {max_power_all} W')
                    ## bottom Limit 
                    if setpoint < minimum_wr:
                        setpoint = minimum_wr
                        print(f'Setpoint auf Minimum: {minimum_wr} W')
                    # send limit
                    if setpoint != old_limit_all:
                        set_limit()
                    
                # no Export
                if grid_sum >= offset_grid:
                    setpoint = max_power_all
                    print(f'no export -> no limit: {setpoint} W')
                    
                    # old limit = new limit
                    if setpoint == old_limit_all:
                        print("Limits identical - not sending Limit")
                    # send limit
                    if setpoint != old_limit_all:
                        set_limit()

            else:
                print("not reachable")
        else:
            print(f"Len max_power: {len(max_power)} or serials incorrect: {len(serials)}")

        sys.stdout.flush() # write out cached messages to stdout
        time.sleep(20) # wait
