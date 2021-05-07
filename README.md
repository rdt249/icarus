# icarus

### Setting up software
Use `git clone github.com/rdt249/icarus` to clone this repository onto a Raspberry Pi.
Make sure the Pi has been set up with the default RES Lab configuration (upgraded to Python 3, installed Jupyter and CircuitPython, etc)

After cloning the repo, the Pi must be configured to launch icarus.py on boot.
Edit crontab with `crontab -e` and add the following lines at the end:
```
# launch icarus script on reboot
@reboot sudo python /home/pi/icarus/icarus.py &
```
Note that the ampersand (&) is important because it lets the Pi continue booting up. Since icarus.py uses an infinite while loop, if the ampersand
is missing the Pi will never finish booting.

The standard increment between pics and data samples is 10 seconds. This can be changed by simply editing `increment` in icarus.py.

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
