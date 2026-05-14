# Capture 6 different exposures of FITS
# during totality phase of eclipse in continuous loop
#       (Exposures in exposure tuple variable)
#                    
# Camera in Still Mode for captures
# resets to Live mode with original exposure/gain/resolution after run
#
# Creates New.txt before first capture to trigger upload program to switch into totallity mode
#   Totality
# Creates New.txt when stopped or error to trigger upload program to return to normal mode
#   End_Totality
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
exposure = ( 0.3, 0.4, 4.0, 40.0, 130.0, 400.0 ) # exposure tuple (ms)
Stop = 0
  
def endprogram():
    global Stop 
    Stop = 1

def Image(camera, exposures, str_date):
    for x in exposures:
        camera.Controls.Exposure.ExposureMs = x
        str_time = time.strftime("%H%M%S", time.gmtime())
        filename = 'totality_'+str_date+'_'+str_time+'_'+str(x)+'ms.fits'
        filepath = str(capture_path / filename)
        camera.CaptureSingleFrameTo(filepath)
   
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
        try:
            with open(str(upload_path / 'totality.txt'),'w') as fw:
                fw.write('This file is the trigger to start totality mode of upload program')
        except:
            pass
        while True:
            if Stop == 1:
                time.sleep(0.5)
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
        with open(str(upload_path / 'end_totality.txt'),'w') as fw:
            fw.write('This file is the trigger to end totality mode of upload program')

if __name__ == '__main__':
    main(SharpCap)
# END OF PROGRAM