# GPS Panel

GPS Panel is a simple web application to present information from your GPS. It depends on gpsd daemon, which reads raw data from your GPS device.


# Installation

GPS Panel is based on [Python Flask](http://flask.pocoo.org/) micro-framework. It has a built-in webserver and by default listens on port 8625. Install the pre-requisites:

```
$ sudo apt-get -y install python-gps
$ sudo -H pip install Flask Flask-SocketIO gevent Pillow
```

or

```
$sudo -H pip install -r requirements.txt 
```

Copy the **gpspanel** folder to /opt directory

# Usage

The GPS Panel can be run as a standalone server. It can be started manually by invoking python:

```
$ cd /opt/gpspanel
$ python gpspanel.py
```

Then using your favorite web browser, go to http://your_ip_address:8625

# Auto Start

To enable the GPS Panel to automatically start after a system reboot, a systemd service file is provided for your convenience:

```
[Unit]
Description=GPS Panel
After=multi-user.target

[Service]
Type=idle
User=astroberry
ExecStart=/usr/bin/python /opt/gpspanel/gpspanel.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

The above service files assumes you copied the gpspanel directory to /opt, so change it to directory you installed gpspanel to on your target system. The user is also specified as **astroberry** and must be changed to your username.

Copy the gpspanel.service file to **/etc/systemd/system**:

```
sudo cp gpspanel.service /etc/systemd/system/
sudo chmod 644 /etc/systemd/system/gpspanel.service
```

Now configure systemd to load the service file during boot:

```
sudo systemctl daemon-reload
sudo systemctl enable gpspanel.service
```

Finally, reboot the system for your changes to take effect:

```
sudo reboot
```

After startup, check the status of the GPS Panel service:

```
sudo systemctl status gpspanel.service
```

If all appears OK, you can start using GPS Panel using any browser.

# Testing

To test GPS Panel while you don't have your GPS connected you can use gps_test.log. Just run gpsfake to emulate gpsd service:

```
gpsfake gps_test.log
```
