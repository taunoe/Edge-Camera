#!/usr/bin/python3

"""
Run:
  python3 lae_pilt.py -p /dev/ttyUSB0 -o ./temp

"""

import os
import sys
import serial
import serial.tools.list_ports as list_ports
from time import sleep
import argparse
import os.path
from array import *
from PIL import Image
import numpy as np
import re
import timeit

dict_Resolutions = {
    'QVGA':     (324, 244),
}

VERSION     = 0
SUBVERSION  = 1

image_count = 0

# For rotating image
def map0(idx, iw, ih):
    return [int(idx%iw), int(idx/iw)]

def map1(idx, iw, ih):
    return [int(idx/ih), ih-int(idx%ih)-1]

def map2(idx, iw, ih):
    return [iw-int(idx%iw)-1, ih-int(idx/iw)-1]

def map3(idx, iw, ih):
    return [iw-int(idx/ih)-1, int(idx%ih)]


def create_bmp(args, rawdata):
  '''
  Saves rawdata to bmp file.
  '''
  start_time = timeit.default_timer()
  global image_count

  (width, height) = dict_Resolutions.get(args.resolution, ("Resolution not supported", 0, 0))

  print("width: {}, height: {}".format(width, height))

  # Image rotate
  if args.spin == 0:
    image_width = width
    map = map0
  elif args.spin == 1:
    image_width = height
    map = map1
  elif args.spin == 2:
    image_width = width
    map = map2
  else:
    image_width = height
    map = map3

  image_height = int((height*width)/image_width)
  print("image_width: {}, image_height: {}".format(image_width, image_height))

  bitmap = np.zeros((image_width, image_height), dtype=np.uint8) # h, w

  # fill up bitmap array - always write u dimension first 
  # (that's how data from the camera was streamed out)
  i = 0
  for pixel in rawdata:
    (u, v) = map(i, image_width, image_height)
    i += 1
    bitmap[u, v] = pixel

  print("i={}px".format(i))

  path = os.path.dirname(args.outputfilepath)
  basename = 'hm01b0'
  outputfile = os.path.join(path, basename + '_' + str(image_count) + '.bmp')

  # Save bitmap
  img = Image.fromarray(bitmap, 'L')
  img.save(outputfile)
  img.show()

  print ("%s created" % (basename + '_' + str(image_count) + '.bmp'))
  image_count += 1
  print("bmp created, time: {}".format(timeit.default_timer() - start_time))


# ***********************************************************************************
#
# Help if serial port could not be opened
#
# ***********************************************************************************
def phase_serial_port_help(args):
    devices = list_ports.comports()

    # First check to see if user has the given port open
    for dev in devices:
        if(dev.device.upper() == args.port.upper()):
            print(dev.device + " is currently open. Please close any other terminal programs that may be using " +
                    dev.device + " and try again.")
            exit()

    # otherwise, give user a list of possible ports
    print(args.port.upper() +
            " not found but we detected the following serial ports:")
    for dev in devices:
        if 'CH340' in dev.description:
            print(
                dev.description + ": Likely an Arduino or derivative. Try " + dev.device + ".")
        elif 'FTDI' in dev.description:
            print(
                dev.description + ": Likely an Arduino or derivative. Try " + dev.device + ".")
        elif 'USB Serial Device' in dev.description:
            print(
                dev.description + ": Possibly an Arduino or derivative.")
        else:
            print(dev.description)


def sync(ser):
  print("sync starts")
  synced = False
  restore_timeout = ser.timeout
  ser.timeout = 0.1 # 0.25
  count = 0
  while(not synced):
    result = ser.read_until(b'\x55')

    print("{} result: {}".format(count, result))
    if(result != b''):
      if(result[len(result)-1] == 85):
                synced = True
    else:
      count += 1

  ser.timeout = restore_timeout
  print("sync ends. ser.timeout={}".format(ser.timeout))


def rawdata_to_txt(args):
  global image_count
  try:
    with serial.Serial(args.port, args.baud) as ser:
      framestart = False
      framestop = False
      ser.reset_input_buffer()
      sync(ser)

      while(True):
        file_name = "img_" + str(image_count) + ".txt"
        with open(file_name, "a") as file:

          try:
            line = ser.readline()
            line = line.decode('utf-8')
          except KeyboardInterrupt:
            exit()

          if line == "+++ frame +++\n":
            start_time = timeit.default_timer()
            framestart = True
            print(line, end='')
            continue
          elif line == '--- frame ---\n':
            framestop = True
            print(line, end='')

          # Image data
          if framestart and not framestop:
            #linelist = re.findall(r"[\w']+", line)
            file.write(line)

          elif framestart and framestop:
            framestart = False
            framestop = False
            image_count += 1
            print("Data > txt, time: {}".format(timeit.default_timer() - start_time))

  except serial.SerialException:
    phase_serial_port_help(args)

  exit()

def rawdata_to_bmp(args):
  try:
    with serial.Serial(args.port, args.baud) as ser:
      rawdata = None
      framestart = False
      framestop = False

      print('Waiting for first frame')
      ser.reset_input_buffer()
      sync(ser)

      while(1): # TODO: allow user to quit gracefully
        line = None
        try:
          line = ser.readline()
          line = line.decode('utf-8')
          # print(line, end='')
        except KeyboardInterrupt:
          exit()

        # Image frame starts
        if line == "+++ frame +++\n":
          start_time = timeit.default_timer()
          framestart = True
          rawdata = []
          count = 0
          print(line, end='')
          continue
        # Image frame ends
        elif line == '--- frame ---\n':
          framestop = True
          print(line, end='')

        # Image data
        if framestart == True and framestop == False:
          
          linelist = re.findall(r"[\w']+", line)

          if len(linelist) != 17:
            print("Droping this frame!")
            framestart = False
            continue

          for item in linelist[1 : ]:
            store = int(item, base=16)
            if(store > 255):
              store = 255
            rawdata.append(store)
          
          count += 1

        elif framestart == True and framestop == True:
          print("count={}",format(count))
          print("rawdata lenght={}px".format(len(rawdata)))
          print("Data ready > bmp, time: {}".format(timeit.default_timer() - start_time))

          create_bmp(args, rawdata)

          framestart = False
          framestop = False

  except serial.SerialException:
    phase_serial_port_help(args)

  exit()


def main():
  parser = argparse.ArgumentParser(
        description = 'This program converts raw data from HM01B0 to bmp files from a serial connection.')

  parser.add_argument('-o', '--output', 
                        dest        = 'outputfilepath',
                        required    = False,
                        help        = 'output file path',
                        metavar     = 'FILEPATH',
                        default     = '.',
                        type        = str
                        )

  parser.add_argument('-p', '--port', 
                        dest        = 'port',
                        required    = True,
                        help        = 'serial port (COM*, /dev/tty*)',
                        metavar     = 'SERIAL_PORT',
                        )

  parser.add_argument('-b', '--baud', 
                        dest        = 'baud',
                        required    = False,
                        help        = 'Baud rate that the board is configured for',
                        type        = int,
                        default     = 460800,
                        )
    
  parser.add_argument('-s', '--spin', 
                    dest        = 'spin',
                    required    = False,
                    help        = 'A number 0-3 for how many times to rotate the image (90 degree increments)',
                    type        = int,
                    default     = 1,
                    )

  parser.add_argument('-r', '--resolution', 
                        dest        = 'resolution',
                        required    = False,
                        help        = 'Resolution',
                        choices     = ['QVGA'],
                        default     = 'QVGA',
                        )

  parser.add_argument('-v', '--version',
                        help        = 'Program version',
                        action      = 'version',
                        version     = '%(prog)s {ver}'.format(ver = 'v%d.%d' %\
                            (VERSION, SUBVERSION))
                        )

  args = parser.parse_args()

  #rawdata_to_bmp(args)
  rawdata_to_txt(args)


if __name__ == "__main__":
  main()
