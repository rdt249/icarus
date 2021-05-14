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

# script config
increment = 10 # time increment in seconds
switch_pin = board.D26 # switch input (active low)
directory = "/home/pi/icarus/"

# init switch
def init_switch():
    global switch
    switch = dio.DigitalInOut(switch_pin) # declare switch pin
    switch.direction = dio.Direction.INPUT # as input

# init camera
def init_camera():
    global camera
    camera = picamera.PiCamera() # declare camera
    camera.resolution = (2592,1944) # max resolution = 2592 x 1944

# init i2c modules
def init_sensors():
    i2c = board.I2C() # init i2c bus
    global baro, hygro, therm
    baro = adafruit_mpl3115a2.MPL3115A2(i2c) # init barometer
    hygro = adafruit_sht31d.SHT31D(i2c) # init hygrometer
    therm = adafruit_mcp9808.MCP9808(i2c) # init thermometer

sensor_header = ["Pressure(Pa)","Altitude(m)","TempBaro(C)",
                 "Humidity(%)","TempHygro(C)","TempTherm(C)"]

def sense(timestamp = None): # read i2c sensors
    # read barometer
    pressure = baro.pressure
    altitude = baro.altitude
    temp_b = baro.temperature
    # read hygrometer
    humidity = hygro.relative_humidity
    temp_h = hygro.temperature
    # read thermometer
    temp_t = therm.temperature
    # format data
    data = [pressure,altitude,temp_b,humidity,temp_h,temp_t]
    if timestamp is not None:
        data = [timestamp] + data
    return data


# init gps - https://learn.adafruit.com/adafruit-ultimate-gps-on-the-raspberry-pi/setting-everything-up
def init_gps():
    os.system("sudo killall gpsd")
    os.system("sudo gpsd /dev/serial0 -F /var/run/gpsd.sock")
    global session
    session = gps.gps("localhost", "2947")
    session.stream(gps.WATCH_ENABLE | gps.WATCH_NEWSTYLE)
    for i in range(4):
        session.next()

gps_header = ["Date(y-m-d)","Time(h:m:s)","TimeError(s)",
              "Latitude(deg)","LatError(deg)","Longitide(deg)","LonError(deg)",
              "Altitude(m)","AltError(m)","Climb(m/s)","ClimbError(m/s)",
              "Track(deg)","TrackError(deg)","Speed(m/s)","SpeedError(m/s)"]
    
def locate(timestamp = None): # read gps - https://gpsd.gitlab.io/gpsd/gpsd_json.html
    report = session.next()
    data = [None] * 15
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
    init_switch()
    init_camera()
    init_sensors()
    init_gps()
    if mode is 1:
        print("mode 1 (ignore switch)")
    if mode is 2:
        print("mode 2 (ignore switch, no images)")
    device = ["System"] + ["MPL3115A2"]*3 + ["SHT31D"]*2 + ["MCP9808"] + ["GPS"]*15
    header = ["Timestamp(s)"] + sensor_header + gps_header
    print(*header,sep='\t')
    while True: # spins forever
        while (switch.value is False) or (mode in [1,2]): # while switch is on
            start = time.time() # record start time
            data = [int(start)] # start with timestamp
            # snap picture
            file_name = directory + "pic/" + str(data[0]) + ".jpg" # format file name
            if mode in [0,1]: # if images should be saved
                camera.capture(file_name) # save pic
            # read i2c sensors
            data += sense()
            # read gps
            data += locate()
            print(*data,sep='\t')
            log(data,header)
            elapsed = time.time() - start # compute elapsed time
            if elapsed < increment: # if increment not exceeded
                time.sleep(increment - elapsed) # wait for increment

# main loop
if __name__ == "__main__": # main function
    if sys.argv[1] is not None: # if input arguments exist
        main(mode = int(sys.argv[1])) # send input argument
    else:
        main() # no input arguments
