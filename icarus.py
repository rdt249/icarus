import board # gpio pins
import digitalio as dio # digital input/output (switches, led, etc)
import busio # gpio busses
import time # timed delays and timestamps
import picamera # camera
import adafruit_sht31d # hygrometer
import adafruit_mcp9808 # thermeter
import adafruit_mpl3115a2 # barometer
import sys # argument vector
import os # navigating file system
import csv # creating and editing csvs
import gps # gps
from func_timeout import func_timeout # a necessary evil

# script config
increment = 10 # time increment in seconds
camera_enabled = True # pictures are saved in icarus/pic, named with a timestamp
beeper_enabled = True # if true, beeper will turn on below the set altitude
beeper_altitude = 140 # if the altitude drops below this level, the beeper turns on
beeper_pin = board.D4 # beeper pin (active high)
led_pin = board.D17 # led output (flashes during every sample)
directory = "/home/pi/icarus/"
    
# init led
def init_led():
    try:
        led = dio.DigitalInOut(led_pin)
        led.direction = dio.Direction.OUTPUT
        led.value = False
        return led
    except:
        print("icarus.init_led() failed")
        return None
    
# init beeper
def init_beeper():
    try:
        beeper = dio.DigitalInOut(beeper_pin)
        beeper.direction = dio.Direction.OUTPUT
        beeper.value = False
        return beeper
    except:
        print("icarus.init_beeper() failed")
        return None

# init camera
def init_camera():
    try:
        camera = picamera.PiCamera() # declare camera
        camera.resolution = (2592,1944) # max resolution = 2592 x 1944
        return camera
    except:
        print("icarus.init_camera() failed")
        return None

# init i2c modules
def init_baro():
    i2c = board.I2C() # init i2c bus
    try:
        baro = adafruit_mpl3115a2.MPL3115A2(i2c) # init barometer
        return baro
    except:
        print("icarus.init_baro() failed")
        return None
    
def init_hygro():
    i2c = board.I2C() # init i2c bus
    try:
        hygro = adafruit_sht31d.SHT31D(i2c) # init hygrometer
        return hygro
    except:
        print("icarus.init_hygro() failed")
        return None

def init_therm():
    i2c = board.I2C() # init i2c bus
    try:
        therm = adafruit_mcp9808.MCP9808(i2c) # init thermometer
        return therm
    except:
        print("icarus.init_therm() failed")
        return None
    
# init gps - https://learn.adafruit.com/adafruit-ultimate-gps-on-the-raspberry-pi/setting-everything-up
def init_gps(timeout = 1):
    # refresh gpsd
    os.system("sudo killall gpsd")
    os.system("sudo gpsd /dev/serial0 -F /var/run/gpsd.sock")
    # init gps
    try:
        session = gps.gps("localhost", "2947")
        session.stream(gps.WATCH_ENABLE | gps.WATCH_NEWSTYLE)
        for i in range(4):
            try:
                func_timeout(1,session.next())
            except:
                return None
        return session
    except:
        print("icarus.init_gps() failed")
        return None
    
# init modules
def init_modules():
    global camera, baro, hygro, therm, session
    camera = init_camera()
    baro = init_baro()
    hygro = init_hygro()
    therm = init_therm()
    session = init_gps()
    return [camera,baro,hygro,therm,session]

sensor_header = ["Pressure(Pa)","Altitude(m)","TempBaro(C)",
                 "Humidity(%)","TempHygro(C)","TempTherm(C)"]

def sense(): # read i2c sensors
    # read barometer
    data = [None] * 6
    if baro is not None:
        data[0] = baro.pressure
        data[1] = baro.altitude
        data[2] = baro.temperature
    # read hygrometer
    if hygro is not None:
        data[3] = hygro.relative_humidity
        data[4] = hygro.temperature
    # read thermometer
    if therm is not None:
        data[5] = therm.temperature
    return data

gps_header = ["Date(y-m-d)","Time(h:m:s)","TimeError(s)",
              "Latitude(deg)","LatError(deg)","Longitide(deg)","LonError(deg)",
              "Altitude(m)","AltError(m)","Climb(m/s)","ClimbError(m/s)",
              "Track(deg)","TrackError(deg)","Speed(m/s)","SpeedError(m/s)"]
    
def locate(): # read gps - https://gpsd.gitlab.io/gpsd/gpsd_json.html
    data = [None] * 15
    if session is None:
        return data
    report = session.next()
    while report['class'] != 'TPV':
        report = session.next()
    if 'time' in report:
        data[0] = report['time'].split("T")[0] # date
        data[1] = report['time'].split("T")[1].split("Z")[0] # time
    if 'ept' in report:
        data[2] = report['ept'] # time error
    if 'lat' in report:
        data[3] = report['lat'] # latitude
    if 'epy' in report:
        data[4] = report['epy'] # latitude error
    if 'lon' in report:
        data[5] = report['lon'] # longitude
    if 'epx' in report:
        data[6] = report['epx'] # longitude error
    if 'alt' in report:
        data[7] = report['alt'] # altitude
    if 'epv' in report:
        data[8] = report['epv'] # altitude error
    if 'climb' in report:
        data[9] = report['climb'] # climb rate
    if 'epc' in report:
        data[10] = report['epc'] # climb error
    if 'track' in report:
        data[11] = report['track'] # track direction
    if 'epd' in report:
        data[12] = report['epd'] # direction error
    if 'speed' in report:
        data[13] = report['speed'] # speed
    if 'eps' in report:
        data[14] = report['eps'] # speed error
    return data
        
def log(data, header, file =  directory + "data/log.csv"): # create or update log given a data row along with a header row
    if os.path.isfile(file) is False: # check if file exists
        with open(file, 'w') as csvfile: # open file in write mode
            filewriter = csv.writer(csvfile,quoting=csv.QUOTE_MINIMAL) # make csv writer
            filewriter.writerow(header) # write column labels
    with open(file,'a') as csvfile: # open file in append mode
        filewriter = csv.writer(csvfile,quoting=csv.QUOTE_MINIMAL) # make csv writer
        filewriter.writerow(data) # write data

def main(mode = 0): # snap pics and collect data
    camera, baro, hygro, therm, session = init_modules()
    led = init_led()
    beeper = init_beeper()
    device = ["System"] + ["MPL3115A2"]*3 + ["SHT31D"]*2 + ["MCP9808"] + ["GPS"]*15
    header = ["Timestamp(s)"] + sensor_header + gps_header
    print(*header,sep='\t')
    while True: # spins forever
        start = time.time() # record start time
        led.value = True
        data = [int(start)] # start with timestamp
        # snap picture
        file_name = directory + "pic/" + str(data[0]) + ".jpg" # format file name
        # read i2c sensors
        data += sense()
        # read gps
        data += locate()
        print(*data,sep='\t')
        log(data,header)
        # check altitude for beeper status
        if data[2] < beeper_altitude and beeper_enabled:
            beeper.value = True
            time.sleep(1)
            beeper.value = False
            time.sleep(4)
            beeper.value = True
            time.sleep(1)
            beeper.value = False
        # get image
        if camera_enabled: # if images should be saved
            camera.capture(file_name) # save pic
        # try to re-init failed modules
        if session is None:
            session = init_gps()
        # wait until increment is over
        led.value = False
        elapsed = time.time() - start # compute elapsed time
        if elapsed < increment: # if increment not exceeded
            time.sleep(increment - elapsed) # wait for increment

# main loop
if __name__ == "__main__": # main function
    main()
