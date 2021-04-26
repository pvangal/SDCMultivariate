import json
import numpy as np
import csv

data = [] # each list in data represents a spectrum
wavelength = []
index = 0
for filename in os.listdir():
    if filename.endswith('.csv'):
        data.append([])
        with open(filename) as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if index == 0:
                    wavelength.append((row[0]))
                data[-1].append(row[1])
            index += 1
timestamps = []
wavelength.remove(wavelength[0])
wavelengths = []
for wave in wavelength:
    wavelengths.append(float(wave))
for column in data:
    timestamps.append((column[0]))
    column.remove(column[0]) # removes the title read from csvfile which is the timestamp
# transpose so that each spectrum is a column in the numpyarray

print (json.dumps(data))