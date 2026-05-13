# Version 2
#
#This program runs on SharpCap 4.0 and 4.1
#
#Captures 15 seconds of .fits files on a 1 minute cadence with
# start at the 15 second of each minute
#offset = 100, gain = 0, resolution = 1000x1000, binning = 1, colourspace = MONO16
#to C:\DEB\date\hold\filename.ser OR folder specified by user in deb.ini
#all other SharpCap settings are at the users discretion
#
#The hold folder is sent to a modified version of Planetary-System-Stacker that
#processes the images with stacking and wavelet correction based on previously determined
#PSS setttings from a config.pss.
#All images in the hold folder are then moved to a Daily_Photosphere folder
#
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
        file.write(image)        
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
    reset_area = scc.Resolution.Value
    reset_folder = ss.CaptureFolder 

    ### Initial Setup ####################################################################
    CleanStop = s.AddCustomButton("STOP", None, None, endprogram)
    try:
        s.TargetName = "daily_photosphere"
        
        ss.UseSubFolders = False
        ss.UseManualTemplates = True 
        ss.ManualSequenceTemplate = '{TargetName}_{Date:ZS}_{Time:U}_{Index}'
        ss.CreateCameraSettingsFile = False

        if not sc.IsTestCamera:
            scc.Binning.Value = '1'
            scc.ColourSpace.Value = 'MONO16'
            scc.BlackLevel.Value = 100
        scc.OutputFormat.Automatic = False
        scc.OutputFormat.Value = 'FITS files (*.fits)'
        scc.FindByName('Frame Rate Limit').Value = '30 fps'
        scc.Gain.Value = 0
        scc.Resolution.Value = '1000x1000'
        # Reset 1000x1000 region of interest (ROI) to the center of the screen
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
                if seconds == 15:
                    str_time = time.strftime("%H%M%S",time.gmtime())
                    str_date = time.strftime("%Y-%m-%d",time.gmtime())
                    capture_path = data_path / str_date / str('photosphere_'+str_date+'_'+str_time)
                    main_path = data_path / str_date
                    capture_path.mkdir(parents=True)
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
                args = PSS_cmd + [str(capture_path), '--post', pss_config_file, '--stack_number', str(stack_image_number)]    
                # Note that we cannot seem to get the output using subprocess.check_output
                # as it fails with invalid handle
                status = subprocess.call(args)
                if status != 0:
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
                ###just upload newest image / skip older for now
                if down_size:
                    args = [config.get('python_version'), str(programs_path / 'down_size.py'),
                            str(uploaded_image.parent), str(uploaded_image.name),
                            str(down_size_percent)]
                    print("down_size:", args)
                    subprocess.call(args)
                    # XXX This ties together the operation of down_size.py ... maybe better 
                    # to have down_size.py be given the output name.
                    image = uploaded_image.with_name(uploaded_image.stem + '_small.jpg')
                    if not image.exists():
                        print("ERROR: downsize failed!", args)
                
                ### create file to start upload
                print("Trying to upload ", image)
                set_upload(str(image))
            else:
                print('No image to upload')
            
            if Stop == 1:
                break
            
           
    finally:
        ### Reset Values and shutdown
        #write_end() # file to signal shutdown of upload program
        s.RemoveCustomButton(CleanStop)
        scc.FindByName('Frame Rate Limit').Value = 'Maximum'
        scc.Resolution.Value = reset_area 
        ss.UseSubFolders = True 
        ss.CaptureFolder = reset_folder 
        ss.UseManualTemplates = False 
        ss.ManualSingleFileTemplate = r'{Date:S}\{TargetName}\{Time}' 
        ss.CreateCameraSettingsFile = True

if __name__ == '__main__':
    main(SharpCap)
    
# END OF PROGRAM

"""
v2 edits: Chris Mandrell, 08/10/2024
1)  Change 'Frame Rate Limit' from 'Maximum' to '30 fps' to reduce memory requirements on long runs

"""
