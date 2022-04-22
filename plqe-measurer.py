import csv
import os
import shutil
import pdfplumber
import pandas
import time

from seabreeze import spectrometers
import numpy as np
import serial

class SBLivePlot(object):
    correct_nonlinearity = True
    correct_dark_counts = True
    _integration_time_ms = 30
    plot_update_ms = 200
    spec = None
    wls = np.array([])
    ax = None
    ani = None
    l = None
    fig = None

    def __init__(self, spec_num=0):
        devs = spectrometers.list_devices()
        try:
            self.spec = spectrometers.Spectrometer(devs[spec_num])
        except Exception as e:
            raise ValueError(f"Can't find a spectrometer, is it powered on and connected? Error message={e}")
        self.integration_time_ms = self._integration_time_ms
        self.update_wls()

    def update_wls(self):
        self.wls = self.spec.wavelengths()
        return self.wls

    @property
    def integration_time_ms(self):
        return self._integration_time_ms

    @integration_time_ms.setter
    def integration_time_ms(self, value):
        try:
            self.spec.integration_time_micros(value * 1000)
            self._integration_time_ms = value
            self.get_counts()  # flush buffer once to forget old data
            self.get_counts()  # flush bufer again to forget in-measurement data
        except Exception as e:
            raise ValueError(f"Error setting integration time to {value}ms: {e}")

    def get_counts(self):
        counts = self.spec.intensities(correct_dark_counts=self.correct_dark_counts, correct_nonlinearity=self.correct_nonlinearity)
        return counts


def set_shutter(port_object, open_state=False, wait_time=1, relay_number=1):
    if open_state == True:
        state_num = 1
    else:
        state_num = 0
    try: 
        port_object.write([255, relay_number, state_num])
    except Exception as e:
        raise ValueError(f"Can't connect with shutter, do you still have ShutterControl running? If so, please close it and try again. Error message={e}")
    time.sleep(wait_time)


def main():
    shutter_control_serial_port = "COM4"
    ser = serial.Serial(shutter_control_serial_port)
    set_shutter(ser, open_state=False)

    sblp = SBLivePlot()
    global dataframe
    dataframe = pandas.DataFrame(columns = ['Sample','PLQE (%)','Optical Density','Peak Center','Peak FWHM','Laser power (mW)'])

    #enter parameters
    input('This program takes PLQE measurements with nonlinearity correction, stray light correction, and common backgrounds. Please make sure the laser is set to the desired power and ShutterControl is closed. Press enter to continue.')
    datadirectory = input("Enter the path to the folder in which you would like to save all of your PLQE results (ex: H:\PLQE):")
    foldername = input("Enter folder name (it will be created):")
    longIT_ms  = int(input("Enter long integration time in ms:"))
    shortIT_ms  = int(input("Enter short integration time in ms:"))
    laserrange = input('Enter laser range (ex: 520 540):')
    plrange = input('Enter PL range (ex: 800 1050):')
    shutterstatedelay = float(input("Enter the time (in s) you want the laser to be illuminating your sample before taking a measurement:"))
    numberofspots = int(input("How many spots do you want to measure for each sample?"))

    def do_measure(int_ms):
        sblp.integration_time_ms = int_ms
        return (sblp.wls, sblp.get_counts())

    def measurebg(foldername, longIT_ms, shortIT_ms, port_object, shutter_wait=1):

        #make folder
        directory = os.path.join(datadirectory,foldername)
        if not os.path.isdir(directory):
            os.makedirs(directory)

        input("Taking background and empty readings - remove sample. Press enter to begin.")
        set_shutter(ser, open_state=False, wait_time=shutter_wait)
        long_bckg_wavelengths, long_bckg_intensities = do_measure(longIT_ms)

        with open(directory+'\\'+"long_bckg.txt","w", newline='') as file:
            writer = csv.writer(file, delimiter='\t')
            for row in zip(long_bckg_wavelengths,long_bckg_intensities):
                writer.writerow(row)

        short_bckg_wavelengths, short_bckg_intensities = do_measure(shortIT_ms)

        with open(directory+'\\'+"bckg.txt","w", newline='') as file:
            writer = csv.writer(file, delimiter='\t')
            for row in zip(short_bckg_wavelengths,short_bckg_intensities):
                writer.writerow(row)    
     
        set_shutter(ser, open_state=True, wait_time=shutter_wait)
        short_empty_wavelengths, short_empty_intensities = do_measure(shortIT_ms)

        with open(directory+'\\'+"empty.txt","w", newline='') as file:
            writer = csv.writer(file, delimiter='\t')
            for row in zip(short_empty_wavelengths,short_empty_intensities):
                writer.writerow(row)

        long_empty_wavelengths, long_empty_intensities = do_measure(longIT_ms)
        set_shutter(ser, open_state=False, wait_time=0)

        with open(directory+'\\'+"long_empty.txt","w", newline='') as file:
            writer = csv.writer(file, delimiter='\t')
            for row in zip(long_empty_wavelengths,long_empty_intensities):
                writer.writerow(row)


    def measurespot(samplename, foldername, longIT_ms, shortIT_ms, spot_num, port_object, shutter_wait=1):
      
        input("Measuring next spot... Enter to continue.")
        spotname = str(spot_num)

        #make folder
        directory = os.path.join(datadirectory,foldername,samplename,spotname)
        if not os.path.isdir(directory):
            os.makedirs(directory)

        input('Taking "in" readings - insert sample at "in" position. Press enter to open shutter and begin.')
        set_shutter(ser, open_state=True, wait_time=shutter_wait)
        long_in_wavelengths, long_in_intensities = do_measure(longIT_ms)

        with open(directory+'\\'+samplename+"_long_in.txt","w", newline='') as file:
            writer = csv.writer(file, delimiter='\t')
            for row in zip(long_in_wavelengths,long_in_intensities):
                writer.writerow(row)    

        short_in_wavelengths, short_in_intensities = do_measure(shortIT_ms)

        with open(directory+'\\'+samplename+"_short_in.txt","w", newline='') as file:
            writer = csv.writer(file, delimiter='\t')
            for row in zip(short_in_wavelengths,short_in_intensities):
                writer.writerow(row)            

        input("Taking out readings - turn sample to 'out' position. Press enter to begin.")
        short_out_wavelengths, short_out_intensities = do_measure(shortIT_ms)

        with open(directory+'\\'+samplename+"_short_out.txt","w", newline='') as file:
            writer = csv.writer(file, delimiter='\t')
            for row in zip(short_out_wavelengths,short_out_intensities):
                writer.writerow(row)    
       
        long_out_wavelengths, long_out_intensities = do_measure(longIT_ms)
        set_shutter(ser, open_state=False, wait_time=0)

        with open(directory+'\\'+samplename+"_long_out.txt","w", newline='') as file:
            writer = csv.writer(file, delimiter='\t')
            for row in zip(long_out_wavelengths,long_out_intensities):
                writer.writerow(row)

        shutil.copy(os.path.join(datadirectory,foldername)+'\\'+"long_bckg.txt", directory)
        shutil.copy(os.path.join(datadirectory,foldername)+'\\'+"bckg.txt", directory)
        shutil.copy(os.path.join(datadirectory,foldername)+'\\'+"long_empty.txt", directory)
        shutil.copy(os.path.join(datadirectory,foldername)+'\\'+"empty.txt", directory)
        
        #run analysis
        analysisprogram = 'python D:/PLQY/PLQE_bw.py --ignore-gooey -st '+str(shortIT_ms)+' -lt '+str(longIT_ms)+' -lr '+str(laserrange)+' -plr '+str(plrange)+' -sp '+str(directory)+'\\'+str(samplename)+'_short_in.txt'+' -lp '+str(directory)+'\\'+str(samplename)+'_long_in.txt'+' -c -cl -sl'
        os.system(analysisprogram)

        #run pdf extraction
        with pdfplumber.open(directory+'\\'+samplename+"_short_fig.pdf") as pdf:
            page = pdf.pages[0]
            text = page.extract_text(x_tolerance=5, y_tolerance=1)

            laserpower_mW = text[(text.index('Laser power: ')+len('Laser power: ')):(text.index('mW'))]
            plqe = text[(text.index('PLQY = ')+len('PLQY = ')):(text.index(' %'))]
            od = text.partition('OD = ')[2].partition(' \n')[0]
            peakpos = text[(text.index('Peak center = ')+len('Peak center = ')):(text.index(' nm'))]
            peakfwhm = text[(text.index('FWHM = ')+len('FWHM = ')):(text.index(' nm',text.index('FWHM = ')))]

            results = {'Sample':samplename,'PLQE (%)':plqe,'Optical Density':od,'Peak Center':peakpos,'Peak FWHM':peakfwhm,'Laser power (mW)':laserpower_mW}

            global dataframe
            dataframe = dataframe.append(results, ignore_index=True)


    def measuresample(foldername, longIT_ms, shortIT_ms, numberofspots, port_object, shutter_wait=1):
        samplename = input("Enter sample name (no spaces):")
        
        spot_num = 1
        for _ in range(numberofspots):
            measurespot(samplename, foldername, longIT_ms, shortIT_ms, spot_num, port_object=port_object, shutter_wait=shutter_wait)
            spot_num=spot_num+1


    #call functions
    measurebg(foldername, longIT_ms, shortIT_ms, port_object=ser, shutter_wait=shutterstatedelay)

    while True: # dynamic number of samples
        goon = input("Type anything to measure more samples (or enter to finish): ")
        if len(goon) == 0:
            break
        measuresample(foldername, longIT_ms, shortIT_ms, numberofspots, port_object=ser, shutter_wait=shutterstatedelay)

    dataframe.to_csv(os.path.join(datadirectory,foldername)+"\\"+foldername+"-datasummary.csv", index = False)
    
    

if __name__ == "__main__":
    main()