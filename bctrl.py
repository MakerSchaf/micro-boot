
from gpiozero import Button, LED
from subprocess import check_call
from time import sleep
from signal import pause


led = LED(19)


def do_led():
    for i in range(0, 3):
        led.on()
        sleep(.2)
        led.off()
        sleep(.2)

def shutdown():
    do_led()
    check_call(['busybox', 'poweroff'])

def reboot():
    do_led()
    check_call(['busybox', 'reboot'])


do_led()

shutdown_btn = Button(20, hold_time = 2)
shutdown_btn.when_held = shutdown

reboot_btn = Button(21, hold_time = 2)
reboot_btn.when_held = reboot

pause()
