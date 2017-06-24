#  Copyright(c) 2017 Radek Kaczorek  <rkaczorek AT gmail DOT com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Library General Public
# License version 2 as published by the Free Software Foundation.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Library General Public License for more details.
#
# You should have received a copy of the GNU Library General Public License
# along with this library; see the file COPYING.LIB.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor,
# Boston, MA 02110-1301, USA.

import gps, time, gevent, base64, cStringIO, math, socket
from gevent import monkey; monkey.patch_all()
from flask import Flask, render_template, request
from flask_socketio import SocketIO
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__, static_folder='assets')
socketio = SocketIO(app)

session = None
thread = None

# define colors for skymap
white = (255, 255, 255)
ltgray = (191, 191, 191)
mdgray = (127, 127, 127)
dkgray = (63, 63, 63)
black = (0, 0, 0)
red = (255, 0, 0)
brightgreen = (0, 255, 0)
darkgreen = (0, 192, 0)
blue = (0, 0, 255)
cyan = (0, 255, 255)
magenta = (255, 0, 255)
yellow = (255, 255, 0)
orange = (255, 128, 0)

def gpsd_connect():
	global session
	while session is None:
		try:
			session = gps.gps("localhost", "2947")
			session.stream(gps.WATCH_ENABLE | gps.WATCH_NEWSTYLE)
		except socket.error:
			print "GPSD server is not available. Retrying in 5 seconds..."
			time.sleep(5)
		except KeyboardInterrupt:
			quit()

	print "GPSD server connected successfully"

def background_thread():
	global session
	while True:
		if session is None:
			gpsd_connect()

		try:
			report = session.next()

			if report['class'] == 'TPV':
				socketio.emit('gpsdata', {
				'mode': report.mode,
				'latitude': report.lat,
				'longitude': report.lon,
				'gpstime': report.time,
				'altitude': report.alt
				})
			if report['class'] == 'SKY':
				socketio.emit('gpsdata', {
				'sats': len(report.satellites),
				'hdop': report.hdop,
				'vdop': report.vdop
				})
				satellites = "<table><tr><th colspan=5 align=left><h2>Visible Satellites<h2></th></tr><tr><th>PRN</th><th>Elevation</th><th>Azimuth</th><th>SS</th><th>Used</th></tr>"
				for s in report.satellites:
					satellites = satellites + "<tr><td>%d</td><td>%d</td><td>%d</td><td>%d</td><td>%s</td></tr>" % (s['PRN'], s['el'], s['az'], s['ss'], s['used'])
				satellites = satellites + "</table>"
				socketio.emit('gpsdata', {
				'satellites': satellites,
				'skymap': skymap(report.satellites)
				})
		except KeyError:
			pass
		except AttributeError:
			pass
		except StopIteration:
			print "GPSD server disconnected"
			session = None
		except KeyboardInterrupt:
			quit()
#		except:
#			pass

		socketio.sleep(1)

def skymap(satellites):
	# set image size
	sz = 400
	
	# create empty image
	img = Image.new('RGBA', (sz, sz), (255,255,255,0))
	draw = ImageDraw.Draw(img)
	draw.chord([(sz * 0.02, sz * 0.02), (sz * 0.98, sz * 0.98)], 0, 360, fill = mdgray, outline = black)
	draw.text((sz/2 * 0.98 - 5, sz * 0.02), "0", fill = ltgray)
	draw.chord([(sz * 0.05, sz * 0.05), (sz * 0.95, sz * 0.95)], 0, 360, fill = dkgray, outline = ltgray)
	draw.text((sz/2 * 0.98 - 5, sz * 0.05), "5", fill = ltgray)

	# azimuth lines
	for num in range(0, 180, 15):
		#turn into radians
		angle = math.radians(num)

		# determine length of radius
		r = sz * 0.95 * 0.5

		# and convert length/azimuth to cartesian
		x0 = int((sz * 0.5) - (r * math.cos(angle)))
		y0 = int((sz * 0.5) - (r * math.sin(angle)))
		x1 = int((sz * 0.5) + (r * math.cos(angle)))
		y1 = int((sz * 0.5) + (r * math.sin(angle)))
		draw.line([(x0, y0), (x1, y1)], fill = ltgray)

	# draw labels
	draw.text((sz * 0.98 / 2 + 8, sz * 0.02 + 1), "N", fill = white)
	draw.text((sz * 0.98 / 2 - 5, sz * 0.98 - 12), "S", fill = white)
	draw.text((sz * 0.98 - 8, sz * 0.98 / 2 + 5), "W", fill = white)
	draw.text((sz * 0.02 + 5, sz * 0.98 / 2 - 8), "E", fill = white)

	
	# elevation lines
	for num in range (15, 90, 15):
		x0 = sz * 0.5 - num * 2
		y0 = sz * 0.5 - num * 2
		x1 = sz * 0.5 + num * 2
		y1 = sz * 0.5 + num * 2
		
		# draw labels
		draw.arc([(x0, y0), (x1, y1)], 0, 360, fill = ltgray)
		draw.text((sz/2 * 0.98 - 10, sz * 0.5 - num * 2), '{:d}'.format(90 - num), fill = ltgray)
	
	# satellites
	for s in satellites:
		if (s['PRN'] != 0) and (s['el'] + s['az'] + s['ss'] != 0) and (s['el'] >= 0 and s['az'] >= 0):
			color = brightgreen
			if s['ss'] < 40:
				color = darkgreen
			if s['ss'] < 35:
				color = yellow
			if s['ss'] < 30:
				color = red
			if s['ss'] < 10:
				color = black


			# circle size
			ssz = 16

			#rotate coords -> 90deg W = 180deg trig
			az = s['az'] + 90
			az = math.radians(az)

			# determine length of radius
			r = sz * 0.98 * 0.5 - ssz
			r -= int(r * s['el'] / 90)

			# convert length/azimuth to cartesian
			x = int((sz * 0.5) - (r * math.cos(az)))
			y = int((sz * 0.5) - (r * math.sin(az)))

			# swap coords
			x = sz * 0.98 - x;

			# draw datellites
			if s['used'] == True:
				draw.chord([(x, y), (x + ssz, y + ssz)], 0, 360, fill = color)
			else:
				draw.arc([(x, y), (x + ssz, y + ssz)], 0, 360, fill = color)

			# draw labels
			draw.text((x + ssz/5, y + ssz/5), '{:2d}'.format(s['PRN']), fill = black)

			# draw legend
			draw.rectangle([(sz - 21, sz - 110), (sz - 1, sz - 10)], fill = brightgreen, outline = black)
			draw.rectangle([(sz - 21, sz - 90), (sz - 1, sz - 10)], fill = darkgreen, outline = black)
			draw.rectangle([(sz - 21, sz - 70), (sz - 1, sz - 10)], fill = yellow, outline = black)
			draw.rectangle([(sz - 21, sz - 50), (sz - 1, sz - 10)], fill = red, outline = black)
			draw.rectangle([(sz - 21, sz - 30), (sz - 1, sz - 10)], fill = black, outline = black)
			draw.text((sz - 19, sz - 105), "40+", fill = black)
			draw.text((sz - 19, sz - 85), "35+", fill = black)
			draw.text((sz - 19, sz - 65), "30+", fill = black)
			draw.text((sz - 19, sz - 45), "30+", fill = black)
			draw.text((sz - 19, sz - 25), "-10", fill = white)

	# encode and return
	imgdata = cStringIO.StringIO()
	img.save(imgdata, format="PNG")
	imgdata_encoded = base64.b64encode(imgdata.getvalue())
	return imgdata_encoded
	

@app.route('/')
def main():
	return render_template('main.html')

@socketio.on('connect')
def handle_connect():
	global thread
	if thread is None:
		thread = socketio.start_background_task(target=background_thread)

if __name__ == '__main__':
	try:
		socketio.run(app, host='0.0.0.0', port = 8625, debug=False)
	except KeyboardInterrupt:
		quit()
