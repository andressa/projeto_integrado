#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Title:       ClosedCaption.py
Author:      Andressa Sivolella <asivolella@poli.ufrj.br>
Date:        2013-05-25
"""

from datetime import datetime
import serial
import redis
import re

USBDEVICE = '/dev/tty.usbmodemfa131'
RESPONSE = {
            0: 'ARDUINO CONNECTED! LETS GET CLOSED CAPTIONS',
            1: 'ARDUINO IS NOT CONNECTED!',
           }
VERBOSE = True
HOST = 'sinatra.twistsystems.com'

class ClosedCaptionHandler(object):
    """
    Package to handle closed caption acquisition from Video Experimenter
    and Arduino Uno
    """
    def __init__(self, usb_device=USBDEVICE, verbose=VERBOSE):
        """
        Initializing object: setting usb path
        """
        self.usb_device = usb_device
        self.redis = redis.Redis(host=HOST)
        self.verbose = verbose
        self.closed_caption = {}

        if not self.open_arduino_conn():
            if self.verbose:
                print RESPONSE[1]
        else:
            if self.verbose:
                print RESPONSE[0]

    def open_arduino_conn(self):
        """
        Start reading usb device output, sent by Arduino
        """
        try:
            self.arduino = serial.Serial(self.usb_device, 57600, timeout=1)
            self.arduino.stopbits = 2
        except serial.serialutil.SerialException:
            return False
        return True

    def start_acquisiton(self):
        try:
            while True:
                try:
                    if (self.arduino.inWaiting() > 0):
                        line = self.arduino.readline()
                        line_str = line.replace('\x00', '')
                        self.redis.publish('cc', '%s: %s' % (datetime.now(), line_str))
                        if self.verbose:
                            print "%s: %s" % (datetime.now(), line_str)
                except serial.serialutil.SerialException:
                    pass
        except KeyboardInterrupt:
            self.stop_acquisition()

    def stop_acquisition(self):
        self.close_arduino_conn()

    def close_arduino_conn(self):
        self.arduino.close()

