#!/usr/bin/python

'''
Info:
 https://www.youtube.com/watch?v=0Kwqdkhgbfw&list=PLtVUYRe-Z-meuAA_NZzmBwwjThfoRzSX6
 https://docs.python.org/3/library/struct.html
 https://en.wikipedia.org/wiki/BMP_file_format

'''

from os import write
import sys # to get the data from the argument
import struct # To unpack the data from the image header

file_name = sys.argv[1]
file_name = file_name.split(".")[0]
print("Filname {}".format(file_name))

# Open file as binary
with open(f'{file_name}.bmp', 'rb') as bmp:
  # Prints byte one by one
  #byte = bmp.read(1)
  #while byte:
  #  print(byte)
  #  byte = bmp.read(1)

  # Getting the offset position 10 -> 4 bytes reads
  bmp.seek(10,0) # start positions
  #offset = bmp.read(4)) # read 4 bytes
  # https://docs.python.org/3/library/struct.html
  raw_offset = bmp.read(4)
  print("RAW offset: {}".format(raw_offset))
  offset = struct.unpack('I', raw_offset)[0] # read 4 bytes, I - unsigned int
  print("offset: {}".format(offset)) # Place where image data begins

  # Get the height and width: position 18, 24 -> 4 bytes reads
  bmp.seek(18, 0)
  raw_bmp_w = bmp.read(4)
  raw_bmp_h = bmp.read(4)
  print("RAW image w: {}, h:{}".format(raw_bmp_w, raw_bmp_h))
  bmp_w = struct.unpack('I', raw_bmp_w)[0]
  bmp_h = struct.unpack('I', raw_bmp_h)[0]
  print("image w: {}, h:{}".format(bmp_w, bmp_h))

  # Get the size: position 34 -> 4 bytes
  bmp.seek(34, 0)
  bmp_s = struct.unpack('I', bmp.read(4))[0]
  print("image s: {}".format(bmp_s)) # size

  # Getting the number of bytes in a row
  bmp_b = int(bmp_s/bmp_h)# Bytes
  print("image b: {}".format(bmp_b)) # Bytes

  # Reading DATA (image)
  bmp.seek(offset, 0)

  bmp_line = ''
  bmp_list = []
  bmp_list_v = []

  for line in range(bmp_h):
    for byte in range(bmp_b):
      bmp_byte = bmp.read(1) # read 1 byte
      char_data = struct.unpack('B', bmp_byte)[0] # B = unsigned char, 0-255
      binary_data = format(char_data, "08b")  # Binary
      reverce_binary_data = 255 - format(char_data, "08b")
      bmp_line += binary_data
    bmp_list.append(bmp_line[:bmp_w])
    bmp_list_v.append(bmp_line[:bmp_w].replace("0", " "))
    bmp_line = '' #

  bmp_list_v.reverse() # pöörab ümber
  for line in bmp_list_v:
    print(line)

# Reshape the data to adjust to n5110
byte_word = ""
n5110_line = []
n5110_array = [] # 2d

for line in range(0, bmp_h, 8):
  for bit_num in range (bmp_w):
    for bit in range(line, line + 8):
      if bit > bmp_h - 1:
        byte_word += 0
      else:
        byte_word += bmp_list[bit][bit_num]

    n5110_line.append(hex(int(byte_word, 2)))
    byte_word = ""
  n5110_array.append(n5110_line)
  n5110_line = []

n5110_array.reverse()

# Save the new array (hex data) in a txt file  (c-code file)
with open(f'{file_name}.txt', 'w') as text_file:
  text_file.write(
    f'static unsigned short {file_name}_rows = {len(n5110_array)};\n'
  )
  text_file.write(
    f'static unsigned short {file_name}_cols = {len(n5110_array[0])};\n'
  )
  text_file.write(
    f'static unsigned char {file_name}[] = \n'
  )
  text_file.write('{\n')
  for line_cnt, lines in enumerate(n5110_array):
    for cnt, hexa in enumerate(lines):
      text_file.write(f'{hexa}')
      if cnt < len(lines)-1:
        text_file.write(',')
    if line_cnt < len(n5110_array)-1:
      text_file.write(f',\n')
    else:
      text_file.write(f'\n')
  text_file.write('};')
  
