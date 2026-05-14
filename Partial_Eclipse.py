
#
#This program runs on SharpCap 4.0 and 4.1
#
#Captures 15 second .ser files on a 1 minute cadence with
#offset = 100, gain = 0, resolution = 1000x1000, binning = 1, colourspace = MONO16
#to C:\DEB\date\Partial\filename.ser
#all other SharpCap settings are at the users discretion
#
#The .ser files are sent to a modified version of Planetary-System-Stacker that
#processes the images with stacking and wavelet correction based on previously determined
#PSS setttings from a config.pss.
#The resultant PSS file is saved to C:\DEB\Upload\filename_gpp.png and
#a sftp config file (instruct.bat) is created for uploading
#
#If image size reduction is requested with 'down_size = True' to 'down_size_percent' value
#the image is sent to 'down_size.py' to be edited and the config file is changed
#
#A sentinel program 'upload.py' is run separately and looks for 'C:\DEB\Upload\new.txt' and 
#'C:\DEB\Upload\end.txt' to make decisions on upload or shutdown behavior
#Uploading is sftp key/pair automated
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

from deb_util import DebConfig

config = DebConfig()
        
partial_ser_time = config.getfloat('partial_ser_time')
interval_sec = config.getfloat('partial_interval_sec', default=60)
down_size = config.getboolean('down_size') #downsize .png gpp images before upload?
down_size_percent = config.getint('down_size_percent') #percentage of original size if down_size True
### setup capture folder structure
str_date = time.strftime("%Y-%m-%d",time.gmtime())
programs_path = Path(config.get('deb_programs'))
data_path = config.data_path()
upload_path = data_path / 'Upload'
capture_path = data_path / str_date / 'Partial'
path_list = [capture_path, upload_path]
# Input for locating PSS and running
search_path = config.get('search_path')
pss_binary = r'C:\Program Files (x86)\PlanetarySystemStacker\PlanetarySystemStacker\planetary_system_stacker.exe'
pss_script = 'planetary_system_stacker.py'
use_pss_binary = False
#PSS settings
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

### SharpCap custom button-STOP function 
def endprogram():
    global Stop
    Stop = 1    
    
### set trigger for upload.py (new.txt)
def set_upload(image):
    '''Store path to image in new.txt for file uploader'''
    new_temp = upload_path / 'new_temp.txt'
    new_ready = upload_path / 'new.txt'
    with new_temp.open('w') as file:
        file.write(str(image))       
    # safeguard against independant programs race condition
    new_temp.replace(new_ready)
''' 
### trigger to end upload.py
def write_end():
    done_path = upload_path / 'end.txt'
    done_path.touch()
'''

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
        sc.LiveView = True
        ss.UseSubFolders = False
        ss.CaptureFolder = str(capture_path)
        ss.UseManualTemplates = True 
        ss.ManualSingleFileTemplate = '{TargetName}_{Exposure}'
        ss.CreateCameraSettingsFile = False

        #Force values
        scc.FindByName('Frame Rate Limit').Value = '15 fps'
        if not sc.IsTestCamera:
            scc.Binning.Value = '1'
            scc.ColourSpace.Value = 'MONO16'
            scc.BlackLevel.Value = 100
        scc.OutputFormat.Automatic = False
        scc.Gain.Value = 0
       
        scc.Resolution.Value = '1000x1000'
        scc.OutputFormat.Value = 'SER file (*.ser)'
        scc.Pan.Value = str(int(int(scc.Resolution.AvailableValues[0].Split('x')[0])/2-500))
        scc.Tilt.Value = str(int(int(scc.Resolution.AvailableValues[0].Split('x')[1])/2-500)) 

        ### Capture images ###################################################################
        Stop = 0
        while True:
            if Stop == 1:
                break
            str_time = time.strftime("%H%M%S",time.gmtime())
            s.TargetName = 'partial_'+str_date + '_'+ str_time
            sc.PrepareToCapture()
            time_start = time.time()
            sc.RunCapture()
            while (time.time() - time_start) < partial_ser_time: 
                if Stop == 1:
                    if sc.Capturing:
                        sc.StopCapture()
                        time.sleep(1)
                    break
                continue
            if sc.Capturing:
                sc.StopCapture()
                
            ### PSS of last capture    
            fname = s.GetLastCaptureFilename()
            args = PSS_cmd + [fname, '--post', pss_config_file, '--stack_number', str(stack_image_number)]    
            # Note that we cannot seem to get the output using subprocess.check_output
            # as it fails with invalid handle
            status = subprocess.call(args)
            if status != 0:
                print('PSS returned error but maybe ok:', status, args)
            processed_image = [ i for i in capture_path.iterdir()
                    if i.match('*gpp*')]
            for image in processed_image:
                uploaded_image = upload_path / image.name
                print("moving ",image, uploaded_image)
                image.rename(uploaded_image)
                
            if Stop == 1:
                break
                
            if processed_image:
                set_upload(uploaded_image)
            else:
                print('No image to upload')
        
            ### Wait until full minute from start of last capture has elapsed before continue
            while (time.time() - time_start) < interval_sec:
                if Stop == 1:
                    break
                continue
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
