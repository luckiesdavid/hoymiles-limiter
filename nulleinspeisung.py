#!/usr/bin/env python3
import requests, time, sys
from requests.auth import HTTPBasicAuth
import logging
from datetime import datetime, timedelta
import os

serials = []
rec_serials = False
max_power = []
rec_max_power = False
setpoint_factor = []
rec_setpoint_factor = False
old_limit = []
rec_old_limit = False
power_each = []
efficency = []
# maximum_wr = 3500  # Maximale Ausgabe des Wechselrichters
minimum_wr = 400  # Minimale Ausgabe des Wechselrichters
offset_grid = -50

dtu_ip = '192.168.178.203'  # IP-Adresse von OpenDTU
dtu_nutzer = 'xxx'  # OpenDTU Nutzername
dtu_passwort = 'xxx'  # OpenDTU Passwort

shelly_ip = '192.168.178.93'  # IP Adresse von Shelly 3EM
hichi_ip = '10.0.1.130'

grid_sum = None
power = None
altes_limit = None
reachable = None
producing = None
setpoint = None
old_limit_all = None

# Logging konfigurieren
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename=os.path.join("logs", f'log_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.log'),  # Name der Log-Datei
    level=logging.INFO,           # Logging-Level (INFO, DEBUG, ERROR, etc.)
    format='%(asctime)s - %(levelname)s - %(message)s'  # Format der Log-Nachrichten
)


def read_opendtu():
    global power, rec_serials, reachable, altes_limit, producing, old_limit, old_limit_all, rec_old_limit
    # Nimmt Daten von der openDTU Rest-API und übersetzt sie in ein json-Format
    r = requests.get(url=f'http://{dtu_ip}/api/livedata/status/inverters').json()
    #print(r)

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
                logging.info(f'Read {len(serials)} Serials at start with: {serials}')
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
        old_limit_all = sum(old_limit)  # sum all limits
    # print(f"Read {old_limit} Inverter Limits ")

    reachable = r['inverters'][0]['reachable']  # Ist DTU erreichbar?
    producing = int(r['inverters'][0]['producing'])  # Produziert der Wechselrichter etwas?
    altes_limit = int(r['inverters'][0]['limit_absolute'])  # Altes Limit
    # power_dc = r['inverters'][0]['AC']['0']['Power DC']['v'] # Lieferung DC vom Panel
    power = r['total']['Power']['v']  # Abgabe BKW AC in Watt
    print("...received opendDTU Data")


def read_maxpower():
    global max_power, rec_max_power
    r = requests.get(url=f'http://{dtu_ip}/api/limit/status').json()
    for i in range(len(serials)):
        # print(max_power)
        # max_power[i] = r[serials[i]]['max_power']
        max_power.append(r[serials[i]]['max_power'])
        rec_max_power = True

def read_efficency():
    global efficency, serials, power_each, power
    efficency = []
    for i in range(len(serials)):
        r = requests.get(url=f'http://{dtu_ip}/api/livedata/status?inv={serials[i]}').json() # http://192.168.178.203/api/livedata/status?inv=1164a00a99df
        e = [inv['AC']['0']['Power']['v'] for inv in r["inverters"]]
        ee = e[0] # list to string
        #power_each.append(ee)
        #power = 500
        #ee = 100
        if power == 0 or ee == 0:
            efficency = [0.25, 0.25, 0.25, 0.25] # identical if reading not possible or 1 inverter = 0W
        else:
            eff = ee / power
            efficency.append(eff)
    print(f"current Efficency : {efficency}")


def inv_factor():
    global max_power_all, setpoint_factor, rec_setpoint_factor
    max_power_all = sum(max_power)
    for i in range(len(serials)):
        setpoint_factor.append(max_power[i] / max_power_all)
    rec_setpoint_factor = True
    print(f"setpoint_factor: {setpoint_factor} ")


def read_shelly():
    global grid_sum
    phase_a = requests.get(f'http://{shelly_ip}/emeter/0', headers={'Content-Type': 'application/json'}).json()['power']
    phase_b = requests.get(f'http://{shelly_ip}/emeter/1', headers={'Content-Type': 'application/json'}).json()['power']
    phase_c = requests.get(f'http://{shelly_ip}/emeter/2', headers={'Content-Type': 'application/json'}).json()['power']
    grid_sum = phase_a + phase_b + phase_c
    print("...received Shelly 3EM Data")


def read_hichi():
    # 'http://10.0.1.130/cm?cmnd=Status%200'
    global grid_sum
    grid_sum = requests.get(f'http://{hichi_ip}/cm?cmnd=Status%200', headers={'Content-Type': 'application/json'}).json()['StatusSNS']['MT681']['Power_cur']


def set_limit():
    global setpoint, efficency
    print(f'Setze Inverterlimit von {round(altes_limit, 1)} W auf {round(setpoint, 1)} W... ')
    logging.info(f'Setze Inverterlimit von {round(altes_limit, 1)} W auf {round(setpoint, 1)} W... ')
    for i in range(len(serials)):
        print(f"setpoint_all: {setpoint} setpoint_each: {setpoint * efficency[i]}")
        logging.debug(f"setpoint_all: {setpoint} setpoint_each: {setpoint * efficency[i]}")
    try:
        for i in range(len(serials)):
            r = requests.post(
                url=f'http://{dtu_ip}/api/limit/config',
                data=f'data={{"serial":"{serials[i]}", "limit_type":0, "limit_value":{setpoint * efficency[i]}}}',
                auth=HTTPBasicAuth(dtu_nutzer, dtu_passwort),
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            #print(r)
            print(f'Konfiguration gesendet ({r.json()["type"]})')
        # print(f"gesendet{setpoint * setpoint_factor[i]}:")
    except Exception as e:
        print(f'Fehler beim Senden der Konfiguration: \n {e}')
        logging.error(f'Fehler beim Senden der Konfiguration: \n {e}')


if __name__ == '__main__':
    while True:
        try:
            read_opendtu()
            # max_power reading only once
            if rec_max_power == False:
                read_maxpower()
            read_shelly()
            #read_hichi()
            if rec_setpoint_factor == False:
                inv_factor()
            read_efficency()
        except Exception as e:
            print(f'Fehler beim Abrufen der Daten {e}')

        ###### Simulation ######
        #reachable = True
        #grid_sum = -1000
        ##altes_limit = 3500 #3500W = kein Limit // 0W = voll Limit
        #power = 2000
        #pv1 = 500
        #pv2 = 500
        #pv3 = 500
        #pv4 = 500
        ##pv_all = []
        #pv_all.append(pv1)
        #pv_all.append(pv2)
        #pv_all.append(pv3)
        #pv_all.append(pv4)
        #print(pv_all)


        # Werte setzen
        print(f"Seriennummern: {serials} mit max_power: {max_power} ")
        print(
            f'\nBezug: {round(grid_sum, 1)} W, Produktion: {round(power, 1)} W, altes_Limit: {round(old_limit_all, 1)} W')
        logging.info(f'Bezug: {round(grid_sum, 1)} W,\t Produktion: {round(power, 1)} W,\t altes_Limit: {round(old_limit_all, 1)} W')


        if len(max_power) & len(serials) == 4:  # ATTENTION HARDCODED 4 INVERTERS!
            if reachable:

                # Export
                if grid_sum < offset_grid:
                    setpoint = (grid_sum + power) - offset_grid  # *-1

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
                logging.error("not reachable")
        else:
            print(f"Len max_power: {len(max_power)} or serials incorrect: {len(serials)}")

        sys.stdout.flush()  # write out cached messages to stdout
        time.sleep(20)  # wait
