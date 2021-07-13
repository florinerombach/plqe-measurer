import seabreeze
from seabreeze.spectrometers import Spectrometer
import csv
import os
import time
import shutil

spec = Spectrometer.from_first_available()

longwait = 5
shortwait = 5
equilibriationtime = 12


def measurebg(foldername, longIT_ms, shortIT_ms):

    #make folder
    directory = os.path.join(os.getcwd(),foldername)
    os.makedirs(directory)

    #take background readings
    input("Taking background readings - remove sample and turn off laser. Press enter to begin.")

    spec.integration_time_micros(1000*longIT_ms)
    time.sleep(longwait)
    long_bckg_wavelengths = spec.wavelengths()
    long_bckg_intensities = spec.intensities(correct_dark_counts=True,correct_nonlinearity=True)

    with open(directory+'\\'+"long_bckg.txt","w", newline='') as file:
        writer = csv.writer(file, delimiter='\t')
        for row in zip(long_bckg_wavelengths,long_bckg_intensities):
            writer.writerow(row)    
    
    spec.integration_time_micros(1000*shortIT_ms)
    time.sleep(shortwait)
    short_bckg_wavelengths = spec.wavelengths()
    short_bckg_intensities = spec.intensities(correct_dark_counts=True,correct_nonlinearity=True)

    with open(directory+'\\'+"bckg.txt","w", newline='') as file:
        writer = csv.writer(file, delimiter='\t')
        for row in zip(short_bckg_wavelengths,short_bckg_intensities):
            writer.writerow(row)    

    #take empty readings
    input("Taking empty readings - remove sample and turn on laser. Press enter to begin.")

    spec.integration_time_micros(1000*shortIT_ms)
    time.sleep(shortwait)
    short_empty_wavelengths = spec.wavelengths()
    short_empty_intensities = spec.intensities(correct_dark_counts=True,correct_nonlinearity=True)

    with open(directory+'\\'+"empty.txt","w", newline='') as file:
        writer = csv.writer(file, delimiter='\t')
        for row in zip(short_empty_wavelengths,short_empty_intensities):
            writer.writerow(row)    

    spec.integration_time_micros(1000*longIT_ms)
    time.sleep(longwait)
    long_empty_wavelengths = spec.wavelengths()
    long_empty_intensities = spec.intensities(correct_dark_counts=True,correct_nonlinearity=True)

    with open(directory+'\\'+"long_empty.txt","w", newline='') as file:
        writer = csv.writer(file, delimiter='\t')
        for row in zip(long_empty_wavelengths,long_empty_intensities):
            writer.writerow(row)


def measurespot(samplename, foldername, longIT_ms, shortIT_ms):
    
    spotname = input("Enter spot name:")

    #make folder
    directory = os.path.join(os.getcwd(),foldername,samplename,spotname)
    os.makedirs(directory)

    #take in readings
    input("Taking in readings - insert sample at 'in' position and turn on laser. Press enter to begin.")

    time.sleep(equilibriationtime)

    spec.integration_time_micros(1000*longIT_ms)
    time.sleep(longwait)
    long_in_wavelengths = spec.wavelengths()
    long_in_intensities = spec.intensities(correct_dark_counts=True,correct_nonlinearity=True)

    with open(directory+'\\'+samplename+"_long_in.txt","w", newline='') as file:
        writer = csv.writer(file, delimiter='\t')
        for row in zip(long_in_wavelengths,long_in_intensities):
            writer.writerow(row)    

    spec.integration_time_micros(1000*shortIT_ms)
    time.sleep(shortwait)
    short_in_wavelengths = spec.wavelengths()
    short_in_intensities = spec.intensities(correct_dark_counts=True,correct_nonlinearity=True)

    with open(directory+'\\'+samplename+"_short_in.txt","w", newline='') as file:
        writer = csv.writer(file, delimiter='\t')
        for row in zip(short_in_wavelengths,short_in_intensities):
            writer.writerow(row)      

    #take out readings
    input("Taking out readings - turn sample to 'out' position and turn on laser. Press enter to begin.")

    spec.integration_time_micros(1000*shortIT_ms)
    time.sleep(shortwait)
    short_out_wavelengths = spec.wavelengths()
    short_out_intensities = spec.intensities(correct_dark_counts=True,correct_nonlinearity=True)

    with open(directory+'\\'+samplename+"_short_out.txt","w", newline='') as file:
        writer = csv.writer(file, delimiter='\t')
        for row in zip(short_out_wavelengths,short_out_intensities):
            writer.writerow(row)    

    spec.integration_time_micros(1000*longIT_ms)
    time.sleep(longwait)
    long_out_wavelengths = spec.wavelengths()
    long_out_intensities = spec.intensities(correct_dark_counts=True,correct_nonlinearity=True)

    with open(directory+'\\'+samplename+"_long_out.txt","w", newline='') as file:
        writer = csv.writer(file, delimiter='\t')
        for row in zip(long_out_wavelengths,long_out_intensities):
            writer.writerow(row)    
            
    shutil.copy(os.path.join(os.getcwd(),foldername)+'\\'+"long_bckg.txt", directory)
    shutil.copy(os.path.join(os.getcwd(),foldername)+'\\'+"bckg.txt", directory)
    shutil.copy(os.path.join(os.getcwd(),foldername)+'\\'+"long_empty.txt", directory)
    shutil.copy(os.path.join(os.getcwd(),foldername)+'\\'+"empty.txt", directory)
    
    #run analysis
    analysisprogram = 'python D:/PLQY/PLQE_bw.py --ignore-gooey -st '+str(shortIT_ms)+' -lt '+str(longIT_ms)+' -lr '+str(laserrange)+' -plr '+str(plrange)+' -sp '+str(directory)+'\\'+str(samplename)+'_short_in.txt'+' -lp '+str(directory)+'\\'+str(samplename)+'_long_in.txt'+' -c -sl -cl'
    os.system(analysisprogram)

def measuresample(foldername, longIT_ms, shortIT_ms, numberofspots):
    
    samplename = input("Enter sample name:")

    for _ in range(numberofspots):
        measurespot(samplename, foldername, longIT_ms, shortIT_ms)
        
#enter parameters
input('Welcome to Flos PLQE measurer! This program takes measurements with nonlinearity correction, stray light correction, and common backgrounds. Press enter to start program.')
foldername = input("Enter folder name (it will be created):")
longIT_ms  = int(input("Enter long integration time in ms:"))
shortIT_ms  = int(input("Enter short integration time in ms:"))
laserrange = input('Enter laser range (ex: 520 540):')
plrange = input('Enter PL range (ex: 800 1050):')
numberofsamples = int(input("How many samples do you want to measure?"))
numberofspots = int(input("How many spots do you want to measure for each sample?"))

#call functions
measurebg(foldername, longIT_ms, shortIT_ms)

for _ in range(numberofsamples): 
    measuresample(foldername, longIT_ms, shortIT_ms, numberofspots)
