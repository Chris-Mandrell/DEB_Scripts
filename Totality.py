# Capture 4 different exposures of FITS
# during totality phase of eclipse
#                    
# Camera in Still Mode for captures
# resets to Live mode with original exposure/gain/resolution after run
#
# Calls HDR_half.py when stopped 
#####################################################################################
from pathlib import Path
import sys

# Add this directory to python path
filedir = str(Path(__file__).parent)
if not filedir in sys.path:
    sys.path.append(filedir)
    
import os
import time
import subprocess
import shutil
from deb_util import DebConfig


config = DebConfig()
    
str_date = time.strftime("%Y-%m-%d",time.gmtime())
data_path = config.data_path()
programs_path = Path(config.get('deb_programs'))
upload_path = data_path / 'Upload'
capture_path = data_path / str_date / 'Totality'
exposure = ( 0.4, 4.0, 40.0, 400.0, 4000.0 ) # exposure tuple (ms)
Stop = 0
  
def endprogram():
    global Stop 
    Stop = 1
    SharpCap.ShowNotification('Totality is processing and shutting down. . .this could take a minute. . .')
    
    ## can't pass arguments to this without screwing up SharpCap
    #  so have to do this over
    config = DebConfig()
    str_date = time.strftime("%Y-%m-%d",time.gmtime())
    programs_path = Path(config.get('deb_programs'))
    data_path = config.data_path()
    upload_path = data_path / 'Upload'
    str_tag = time.strftime("%Y-%m-%d_%H%M%S")
    image = 'hdr_'+str_tag+'.jpg'
    
    args = [config.get('python_version'), str(programs_path / 'HDR_half.py'), image, str_date]   
    subprocess.call(args)



def Image(camera, exposures, str_date):
    for x in exposures:
        camera.Controls.Exposure.ExposureMs = x
        str_time = time.strftime("%H%M%S", time.gmtime())
        filename = 'totality_'+str_date+'_'+str_time+'_'+str(x)+'ms.fits'
        filepath = str(capture_path / filename)
        camera.CaptureSingleFrameTo(filepath)


### set trigger for upload.py (new.txt)
def set_upload(image):
    check_busy = 1
    while check_busy:
        try:
            with open(str(upload_path / 'new_temp.txt'),'w') as file:
                file.write(image)        
            check_busy = 0
        except:
            pass
    # another safeguard against independant programs race condition
    shutil.move(str(upload_path / 'new_temp.txt'), str(upload_path / 'new.txt'))
    
def main(s):
    
    ss = s.Settings
    sc = s.SelectedCamera
    scc = sc.Controls
    
    quick_test = sc.IsTestCamera
    
    #reset values for returning to live mode at end of collection
    reset_exp = scc.Exposure.Value
    reset_area = scc.Resolution.Value

    ### Initial Setup ####################################################################
    CleanStop = s.AddCustomButton("STOP", None, None, endprogram)
   
    try:
        sc.LiveView = False # need to reset
        ss.CreateCameraSettingsFile = False # need to reset

        #Forced values
        if not quick_test:
            scc.Binning.Value = '1'
            scc.ColourSpace.Value = 'MONO16'
            scc.BlackLevel.Value = 100
        scc.OutputFormat.Automatic = False
        scc.OutputFormat.Value = 'FITS files (*.fits)'
        scc.Resolution.Value = scc.Resolution.AvailableValues[0]
        scc.Gain.Value = 0

        ### Capture images ####################################################################
        while True:
            if Stop == 1:
                break
            Image(sc, exposure, str_date)

    finally:
        ### Return SharpCap to live mode with reset values #####################################
        s.RemoveCustomButton(CleanStop)
        ss.CreateCameraSettingsFile = True
        sc.LiveView = True
        scc.Resolution.Value = reset_area
        scc.Exposure.Value = reset_exp
        s.ShowMessageBox('Totality has successfully shutdown')

if __name__ == '__main__':
    main(SharpCap)
# END OF PROGRAM