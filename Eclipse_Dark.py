# Capture DARKS
# 64 count each exposure          
#
# Camera in Still Mode for captures
# resets to Live mode with original exposure/resolution
#####################################################################################
import time
from pathlib import Path
import sys

# Add this directory to python path
filedir = str(Path(__file__).parent)
if not filedir in sys.path:
    sys.path.append(filedir)

from deb_util import DebConfig

config = DebConfig()
data_path = config.data_path()

str_date = time.strftime("%Y-%m-%d",time.gmtime())
capture_path = data_path / str_date / 'Darks' # path for capture folder
number_images = 64
exposure = ( 0.3, 0.4, 4.0, 40.0, 130.0, 400.0 ) # exposure tuple (ms)   

if __name__ == '__main__':
#def main():

    s = SharpCap
    ss = s.Settings
    sc = s.SelectedCamera
    scc = sc.Controls

    ### Initial Setup ####################################################################
    sc = s.Cameras[0]
    if sc.CanRunInLiveMode:
        sc.LiveView = False

    #reset values for returning to live mode at end of collection
    reset_exp = scc.Exposure.Value
    if scc.Resolution.Available:
        reset_area = scc.Resolution.Value

    #Forced values
    if scc.Binning.Available:
        if '1' in scc.Binning.AvailableValues:
            scc.Binning.Value = '1'
    scc.OutputFormat.Automatic = False
    if 'FITS files (*.fits)' in scc.OutputFormat.AvailableValues:
        scc.OutputFormat.Value = 'FITS files (*.fits)'
    if scc.ColourSpace.Available:
        if 'MONO16' in scc.ColourSpace.AvailableValues:
            scc.ColourSpace.Value = 'MONO16'
    if scc.Resolution.Available:
        scc.Resolution.Value = scc.Resolution.AvailableValues[0]

    ### Capture DARKS ####################################################################
    for x in exposure:
        for i in range(number_images):       
            scc.Exposure.ExposureMs = x
            sc.CaptureSingleFrameTo(str(capture_path / f'dark_{str_date}_{x}ms_{i+1}.fits'))
            ss.CreateCameraSettingsFile = False
        ss.CreateCameraSettingsFile = True

    ### Reset SharpCap to live mode with appropriate exposure #############################  
    ss.CreateCameraSettingsFile = True   
    if sc.CanRunInLiveMode:
        sc.LiveView = True
    if scc.Resolution.Available:
        scc.Resolution.Value = reset_area
    if scc.Exposure.Available:
        scc.Exposure.Value = reset_exp 

# END OF PROGRAM
