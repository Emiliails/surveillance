import RPi.GPIO as GPIO
import time

# pin11
BuzzerPin = 11

def setup_buzzer():
	global BuzzerPin
	GPIO.setmode(GPIO.BOARD)       # Numbers GPIOs by physical location
	GPIO.setup(BuzzerPin, GPIO.OUT)
	GPIO.output(BuzzerPin, GPIO.HIGH)

def start_buzzer():
	GPIO.output(BuzzerPin, GPIO.LOW)	
	#低电平是响
def stop_buzzer():
	GPIO.output(BuzzerPin, GPIO.HIGH)
	#高电平是停止响
def beep(x):    #响3秒后停止3秒
	start_buzzer()
	time.sleep(x)
	stop_buzzer()
	time.sleep(x)

def loop():
	while True:
		beep(3)

def destroy_buzzer():
	GPIO.output(BuzzerPin, GPIO.HIGH)
	GPIO.cleanup()                     # Release resource

if __name__ == '__main__':     # Program start from here
	setup_buzzer()
	try:
		loop()
	except KeyboardInterrupt:  # When 'Ctrl+C' is pressed, the child program destroy() will be  executed.
		destroy_buzzer()
