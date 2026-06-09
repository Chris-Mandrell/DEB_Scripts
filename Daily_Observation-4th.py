"""IronPython program for SharpCap capture of daily solar images
Copyright (C) 2024  Dynamic Eclipse Broadcast (DEB) Initiative

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

# 
#This program runs on SharpCap 4.0 and later
#
#Captures 15 seconds of .fits files on a 1 minute cadence with
# start at the 45 second of each minute
#offset = 100, gain = 0, resolution = 1000x1000, binning = 1, colourspace = MONO16
#to C:\DEB\date\hold\filename.ser OR folder specified by user in deb.ini
#all other SharpCap settings are at the users discretion
#
#The hold folder is sent to a modified version of Planetary-System-Stacker that
#processes the images with stacking and wavelet correction based on previously determined
#PSS setttings from a config.pss.
#All images in the hold folder are then moved to a Daily_Photosphere folder
#
#The resultant PSS file is saved and a sftp config file (instruct.bat) is created for uploading
#
#If image size reduction is requested with 'down_size = True' to 'down_size_percent' value
#the image is sent to 'down_size.py' to be edited and the config file is changed
#
#A sentinel program 'upload.py' is run separately and looks for 'new.txt' and 
#'end.txt' to make decisions on upload or shutdown behavior
#Uploading is sftp key/pair automated
#
# file/program locations controlled by deb configuration in C:\Users\user_name\deb.ini
#
# Author:   Chris Mandrell, SIUC, Dynamic Eclipse Broadcast Initiative
#           Castor Fu, Dynamic Eclipse Broadcast Initiative
# Created: 4/2024
#####################################################################################

from pathlib import Path
import sys

# Add this directory to python path
filedir = str(Path(__file__).parent)
if not filedir in sys.path:
    sys.path.append(filedir)

import time
import os
import shutil
import subprocess
import sys
import os.path

from SharpCap.UI import CaptureLimitType

from deb_util import DebConfig

config = DebConfig()
        
partial_ser_time = config.getfloat('partial_ser_time') # remnant from original eclipse build
interval_sec = config.getfloat('partial_interval_sec', default=60) # remnant from original eclipse build
### setup capture folder structure
str_date = time.strftime("%Y-%m-%d",time.gmtime())
programs_path = Path(config.get('deb_programs'))
data_path = config.data_path()
main_path = data_path / str_date
processed_path = data_path / str_date / 'Daily_Photosphere'
upload_path = data_path / 'Upload'
path_list = [processed_path]
# Input for locating PSS and running
search_path = config.get('search_path')
pss_binary = r'C:\Program Files (x86)\PlanetarySystemStacker\PlanetarySystemStacker\planetary_system_stacker.exe'
pss_script = 'planetary_system_stacker.py'
use_pss_binary = False
#PSS settings
down_size = config.getboolean('down_size') #downsize .png gpp images before upload?
down_size_percent = config.getint('down_size_percent') #percentage of original size if down_size True
pss_config_file = str(programs_path / 'deb_config.pss')
stack_image_number = 80
##########################################################################################################################

### Build folder structure
try:
    for path in path_list:
        path.mkdir(parents=True)
except FileExistsError:
    pass

def find_pss(path, name, use_binary=False):
    """ Search for PSS - will be in  configuration file later probably
    also updates python_version and search_path to trim if necessary
    """
    docfile = Path(pss_binary).parent.parent / 'README_DEB.md'
    if use_binary and docfile.exists():
        return [pss_binary]
    else:
        result = []
        for root, dir, files in os.walk(path):
            if name in files:     
                result.append(os.path.join(root, name))
        if not result:
            raise ValueError("No file found matching {}".format(name))
        pss_script = result[0]
        py_binary = find_python(pss_script)
        if py_binary is None:
            raise ValueError("No python found!")
        py_dir = str(Path(py_binary).parent)
        if py_binary != config.get('python_version') or search_path != py_dir:
            config.set_value('python_version', py_binary)
            python_version = py_binary
            config.set_value('search_path', py_dir)
            config.save_config()
        return [py_binary, pss_script]

def find_python(path):
    """Locate python interpreter for a given source file or returns None"""
    for p in Path(path).parents:
        py = p / 'python.exe'
        if py.exists():
            return str(py)
            
def move_hold(source_dir, target_dir):
    file_names = os.listdir(source_dir)
    for file in file_names:
        shutil.move(os.path.join(source_dir, file), target_dir)
    os.rmdir(source_dir)

### set trigger for upload.py (new.txt)
def set_upload(image):
    '''Store path to image in new.txt for file uploader'''
    new_temp = upload_path / 'new_temp.txt'
    new_ready = upload_path / 'new.txt'
    with new_temp.open('w') as file:
        file.write(str(image))        
    # safeguard against independant programs race condition
    new_temp.replace(new_ready)
    
### SharpCap custom button-STOP function 
def endprogram():
    global Stop
    Stop = 1    

def main(s):
    global Stop
    global partial_ser_time
    global stack_image_number
    
    PSS_cmd = find_pss(search_path, pss_script)
    print('Using stacker:', PSS_cmd)

    ss = s.Settings
    sc = s.SelectedCamera
    scc = sc.Controls
    
    from SharpCap.Base import NotificationStatus
    startInfo = subprocess.STARTUPINFO()
    startInfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startInfo.wShowWindow = subprocess.SW_HIDE
    
    print('Camera ', sc.DeviceName, ' selected')
    quick_test = False

    # Note that SharpCap has two different test cameras
    # we might be able to use them for testing, but it's not really been
    # tested for that.
    if sc.IsTestCamera:
        quick_test = True

    if quick_test:
        partial_ser_time = 1.0
        stack_image_number = 2
   
    #reset values for returning at end of collection
    if scc.Resolution.Available:
        reset_area = scc.Resolution.Value
    reset_folder = ss.CaptureFolder 

    ### Initial Setup ####################################################################
    CleanStop = s.AddCustomButton("STOP", None, None, endprogram)
    try:
        if 'FITS files (*.fits)' in scc.OutputFormat.AvailableValues:
            scc.OutputFormat.Value = 'FITS files (*.fits)'
        else:
            raise ValueError(".fits format not available for this camera")
            
        s.TargetName = "daily_photosphere"
        
        ss.UseSubFolders = False
        ss.UseManualTemplates = True 
        ss.ManualSequenceTemplate = '{TargetName}_{Date:ZS}_{Time:U}_{Index}'
        ss.CreateCameraSettingsFile = False

        if not sc.IsTestCamera:
            if scc.Binning.Available:
                if '1' in scc.Binning.AvailableValues:
                    scc.Binning.Value = '1'
            if scc.ColourSpace.Available:
                if 'MONO16' in scc.ColourSpace.AvailableValues:
                    scc.ColourSpace.Value = 'MONO16'
            if scc.BlackLevel.Available:
                scc.BlackLevel.Value = 100
        scc.OutputFormat.Automatic = False
        if scc.FindByName('Frame Rate Limit').Available:
            scc.FindByName('Frame Rate Limit').Value = '30 fps'
        if scc.Gain.Available:
            scc.Gain.Value = 0
        if scc.Resolution.Available:
            if '1000x1000' in scc.Resolution.AvailableValues or 'Custom...' in scc.Resolution.AvailableValues:
                scc.Resolution.Value = '1000x1000'
        # Reset 1000x1000 region of interest (ROI) to the center of the screen
        if scc.Pan.Available and scc.Tilt.Available:
            scc.Pan.Value = str(int(int(scc.Resolution.AvailableValues[0].Split('x')[0])/2-500))
            scc.Tilt.Value = str(int(int(scc.Resolution.AvailableValues[0].Split('x')[1])/2-500)) 
        
        ### Capture images ###################################################################
        Stop = 0
        while True:
            if Stop == 1:
                break
            
            while True:
                if Stop == 1:
                    break
                seconds = time.localtime()[5]
                if seconds == 45:
                    str_time = time.strftime("%H%M%S",time.gmtime())
                    str_date = time.strftime("%Y-%m-%d",time.gmtime())
                    capture_path = data_path / str_date / str('photosphere_'+str_date+'_'+str_time)
                    capture_path.mkdir(parents=True)
                    main_path = data_path / str_date
                    ss.CaptureFolder = str(capture_path)
                    sc.CaptureConfig.CaptureLimitType = CaptureLimitType.TimeLimited
                    sc.CaptureConfig.CaptureLimitValue = 15
                    sc.PrepareToCapture()
                    sc.RunCapture()
                    while(sc.Capturing):
                        if Stop == 1:
                            break
                        continue
                    break
                
            ### PSS of last capture
            if Stop != 1:
                s.ShowNotification("Attempting PSS sharpening of {}".format(str(capture_path)))
                args = PSS_cmd + [str(capture_path), '--post', pss_config_file, '--stack_number', str(stack_image_number)]    

                status = subprocess.call(args, startupinfo=startInfo)
                if status != 0:
                    s.ShowNotification("PSS encountered an error while processing {}".format(str(capture_path)), NotificationStatus.Error)
                    print('PSS returned error but maybe ok:', status, args)
            try:
                move_hold( str(capture_path), str(processed_path) )        
            except: pass
            
            ###############################uploading#############################
            processed_image = [ i for i in main_path.glob('*gpp*')]
            for image in processed_image:
                uploaded_image = upload_path / image.name
                print("moving ",image, uploaded_image)
                image.rename(uploaded_image)
                
            if Stop == 1:
                break
                
            if processed_image:
                set_upload(uploaded_image)
                s.ShowNotification("PSS successfully processed {}".format(str(capture_path)), NotificationStatus.OK)
            else:
                print('No image to upload')
                s.ShowNotification("PSS was unable to process {}".format(str(capture_path)), NotificationStatus.Warning)
            if Stop == 1:
                break
    except ValueError as e:
        print("Fatal error that terminated the program: {}".format(e))
           
    finally:
        ### Reset Values and shutdown
        #write_end() # file to signal shutdown of upload program
        s.RemoveCustomButton(CleanStop)
        if scc.FindByName('Frame Rate Limit').Available:
            scc.FindByName('Frame Rate Limit').Value = 'Maximum'
        if scc.Resolution.Available:
            if '1000x1000' in scc.Resolution.AvailableValues or 'Custom...' in scc.Resolution.AvailableValues:
                scc.Resolution.Value = reset_area 
        ss.UseSubFolders = True 
        ss.CaptureFolder = reset_folder 
        ss.UseManualTemplates = False 
        ss.ManualSingleFileTemplate = r'{Date:S}\{TargetName}\{Time}' 
        ss.CreateCameraSettingsFile = True

if __name__ == '__main__':
    main(SharpCap)
    
# END OF PROGRAM

