# GPS Panel

GPS Panel is a simple web application to present information from your GPS. It depends on gpsd daemon, which reads raw data from your GPS device.


# Installation

GPS Panel is based on [Python Flask](http://flask.pocoo.org/) micro-framework. It has a built-in webserver and by default listens on port 8625. Install the pre-requisites:

```
$sudo pip3 install -r requirements.txt 
```

Copy the **gpspanel** folder to  **DIRECTORY** (eg. /var/www/)

# Usage

The GPS Panel can be run as a standalone server. It can be started manually by invoking python:

```
$ python3 DIRECTORY/gpspanel/gpspanel.py
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
User=nobody
ExecStart=/usr/bin/python3 DIRECTORY/gpspanel/gpspanel.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

The above service files assumes you copied the gpspanel directory to **DIRECTORY** - replace **DIRECTORY** with real path to gpspanel on your system.

Copy the gpspanel.service file to **/etc/systemd/system**:

```
sudo cp gpspanel.service /etc/systemd/system/
sudo chmod 644 /etc/systemd/system/gpspanel.service
```

Now configure systemd to load the service file during boot:

```
sudo systemctl daemon-reload
sudo systemctl enable gpspanel.service
sudo systenctl start gpspanel.service
```

After startup, check the status of the GPS Panel service:

```
sudo systemctl status gpspanel.service
```

If all appears OK, you can start using GPS Panel using any browser.

# Testing

To test GPS Panel while you don't have your GPS connected you can use gps_test.log. Just run gpsfake in your terminal to emulate gpsd service:

```
gpsfake -c 1 gps_test.log
```
