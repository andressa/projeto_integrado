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
import json

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
                        try:
                            cc_data = self.parse(line_str)
                        except:
                            cc_data = self._get_json_format()[ 'text' ] = line_str
                        cc_data['timestamp'] = datetime.now()
                        self.redis.publish('cc',  json.dumps(cc_data))
                        if self.verbose:
                            print cc_data
                except serial.serialutil.SerialException:
                    pass
        except KeyboardInterrupt:
            self.stop_acquisition()

    def stop_acquisition(self):
        self.close_arduino_conn()

    def close_arduino_conn(self):
        self.arduino.close()

    def _get_json_format(self):
        return {
        'speaker': {
            'name': '',
            'type': ''
            },
        'text': '',
        'timestamp': ''
        }


    def parse(self, line):
        '''
        A mudança de um speaker é dado pelo símbolo >>, quando
        há um diálogo entre duas pessoas, ou por >>>, quando
        várias estão falando.
        obs: por amostragem, vi que esse padrão não é bem respeitado.
        para contornar esse problema estou fazendo da seguinte forma:
        começa com >> é simples, mais que isso (>>>, >>>>), é múltiplo.

        Em seguida vem o nome do speaker. Ele pode ser identificado
        como o nome antes de :, pode ser que não seja identificado e
        pode estar entre [].

        O texto vem a seguir
        Caso as linhas não comecem com >> ou >>> serão tratadas como
        continuação do texto.

        Por sim, linhas entre [] são as que passam uma ação, como [APLAUSOS]
        '''

        speaker_re = re.compile(r'^>> |^>>> ')
        name_re = re.compile(r'^\[([a-zA-Z ]+)\] |^([a-zA-Z ]+): ')

        data = self._get_json_format()

        # Define speaker
        # Search for pattern
        speaker = speaker_re.search(line)
        new_str = ''
        if speaker:
            # Type
            if speaker.group() == '>> ': data['speaker']['type'] = 'simple'
            else: data['speaker']['type'] = 'multiple'
            # Name
            # It will only be available in case there is a speaker
            # Remove the >> ...
            new_str = speaker_re.split(line)[1]
            # ... and search in the new string
            name = name_re.search(new_str)
            # If there is a name it can be in the first or second group
            if name: data['speaker']['name'] = name.group(1) or name.group(2)

        # Get text
        if new_str:
            data['text'] = name_re.split(new_str)[-1]
        else:
            data['text'] = line

        return data

