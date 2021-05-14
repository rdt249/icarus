![drawing](https://scp-com.s3.amazonaws.com/314a1a15/University_of_Tennessee_at_Chattanooga_logo.svg.png)
<br>
![drawing](https://i.imgur.com/GIZFPgy.png)

# icarus
_an Intelligent, Cheap, And Reliable University Satellite_

![drawing](https://images.vexels.com/media/users/3/126635/isolated/preview/87fabfeab4b01aa3d5338bf1c0c67fe6-2-open-logo-wings-02-by-vexels.png)

### Installing dependencies

```
sudo apt-get install gpsd gpsd-clients
sudo pip install gps
```

### Setting up software
First clone this repo onto the Raspberry Pi:
```
git clone https://github.com/rdt249/icarus
```
Make sure the Pi has been set up with the default RES Lab configuration (upgraded to Python 3, installed Jupyter and CircuitPython, etc)

Next you need to install the Python libraries used by the icarus.py script. If `sudo python icarus.py` runs without error, you're good to go. If not, you should install each of the dependencies manually:
```
sudo apt-get install gpsd gpsd-clients python-gps
sudo pip install gps
sudo pip install adafruit_circuitpython_mcp9808
sudo pip install adafruit_circuitpython_sht31d
sudo pip install adafruit_circuitpython_mpl3115a2
```
Now that all the dependencies are install, the Pi can be configured to launch icarus.py on boot.
Edit crontab with `crontab -e` and add the following lines at the end:
```
# launch icarus script on reboot
@reboot sudo python /home/pi/icarus/icarus.py &
```
Note that the ampersand (&) is important because it lets the Pi continue booting up. Since icarus.py uses an infinite while loop, if the ampersand
is missing the Pi will never finish booting.

The standard increment between pics and data samples is 10 seconds. This can be changed by simply editing `increment` in icarus.py.

The camera and GPS will not be usable by any other scripts while icarus.py is running in the background. To kill the script use:
```
sudo pkill -9 -f icarus.py
```
If that doesn't work, you could bust out the sledge hammer: `sudo killall python`

### Setting up hardware

Besides obvious things like the camera, sensors, and power supply, there is only one other step for setting up the Pi.
The main loop in icarus.py is disabled unless pin 26 on the GPIO is grounded. The best way to do this is with a SPDT switch.
Alternatively you could use a pullup resistor plus a button to manually initiate samples, or just a simple jumper.

This feature can be disabled via input arguments when icarus.py is called. Set up input arguments by editing the line in crontab:
```
# launch icarus script on reboot
@reboot sudo python /home/pi/icarus/icarus.py X &
```
If X = 1, the Pi will take pics and record data regardless of value on pin 26.
If X = 2, the Pi will record data regardless of pin 26, without pictures.

### Running icarus inside a Python script or Jupyter Notebook

If icarus.py is running in the background, make sure to kill it first (see above).
Running the main icarus loop can be done within a Python script or notebook with the following lines:
```
import icarus
icarus.main() # start main icarus loop
```
To pass input arguments (see above), use the optional input `main`.
```
icarus.main(mode=1) # start main icarus loop ignoring switch
icarus.main(mode=2) # start main icarus loop ignoring switch and without pictures
```
After importing icarus, you can also use the functions in icarus.py such as sense(), locate(), and log():
```
import icarus, time
timestamp = int(time.time()) # get timestamp
sensor_data = icarus.sense() # read i2c sensors
gps_data = icarus.locate() # read gps data
data = [timestamp] + sensor_data + gps_data # format data
header = ["Timestamp(s)"] + icarus.sensor_header + icarus.gps_header # format header
icarus.log(data,header) # creates or updates csv log at icarus/data/log.csv
```
