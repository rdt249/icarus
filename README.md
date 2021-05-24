![drawing](https://scp-com.s3.amazonaws.com/314a1a15/University_of_Tennessee_at_Chattanooga_logo.svg.png)
<br>
![drawing](https://i.imgur.com/GIZFPgy.png)

# icarus
_an Intelligent, Cheap, And Reliable University Satellite_

![drawing](https://images.vexels.com/media/users/3/126635/isolated/preview/87fabfeab4b01aa3d5338bf1c0c67fe6-2-open-logo-wings-02-by-vexels.png)

### Setting up software
First clone this repo onto the Raspberry Pi:
```
git clone https://github.com/rdt249/icarus
```
Make sure the Pi has been set up with the default RES Lab configuration (upgraded to Python 3, installed Jupyter and CircuitPython, etc). Also make sure that all the necessary interfaces are enabled, namely: SSH, Camera, I2C, and Serial Port (these can be enabled via `sudo raspi-config`).

Next you need to install the Python libraries used by the icarus.py script. If `sudo python icarus.py` runs without error, you're good to go. If not, you should install each of the dependencies manually:
```
sudo apt-get install gpsd gpsd-clients python-gps
sudo pip install adafruit_circuitpython_mcp9808
sudo pip install adafruit_circuitpython_sht31d
sudo pip install adafruit_circuitpython_mpl3115a2
```
And then set up the GPS daemon:
```
sudo gpsd /dev/serial0 -F /var/run/gpsd.sock
```
If you have issues with the GPS, check out [this Adafruit guide](https://learn.adafruit.com/adafruit-ultimate-gps-hat-for-raspberry-pi/use-gpsd).
Now reboot the Pi. Now that all the dependencies are installed, the Pi can be configured to launch icarus.py on boot.
Edit crontab with `crontab -e` and add the following lines at the end:
```
# launch icarus script on reboot
@reboot sudo python /home/pi/icarus/icarus.py &
```
Note that the ampersand (&) is important because it lets the Pi continue booting up. Since icarus.py uses an infinite while loop, if the ampersand
is missing the Pi will never finish booting.

The standard increment between pics and data samples is 10 seconds. This can be changed by simply editing `increment` in icarus.py.

The camera and GPS will not be usable by any other scripts while icarus.py is running in the background. List all background Python scripts with `ps -fA | grep python`. To kill the script use:
```
sudo pkill -9 -f /home/pi/icarus/icarus.py
```
If that doesn't work, you could bust out the sledge hammer: `sudo killall python`

### Using icarus.py inside another Python script or a Jupyter Notebook

If icarus.py is running in the background, make sure to kill it first (see above).
Running the main icarus loop can be done within a Python script or notebook with the following lines:
```
import icarus
icarus.main() # start main loop
```
You can edit parameters before calling `main()` to configure your flight (below are the default configurations):
```
import icarus
icarus.increment = 10 # seconds between each sample and pic
icarus.camera_enabled = True # enable/disable camera
icarus.beeper_enabled = True # enable/disable beeper
icarus.beeper_altitude = 1000 # if the device drops below this altitude (in meters), the beeper turns on
icarus.beeper_pin = board.D4 # beeper pin (active high)
icarus.led_pin = board.D17 # led output (flashes during every sample)
icarus.directory = "/home/pi/icarus/" # inside the directory folder, there should be subfolders named "pic" and "data"
icarus.main() # start main loop
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
