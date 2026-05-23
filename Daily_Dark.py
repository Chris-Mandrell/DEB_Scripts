# Capture DARKS
# 128 count at user exposure/offset/gain         
#
# Camera in Still Mode for captures
# resets to Live mode with original resolution
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
capture_path = data_path / str_date / 'Darks_1000x1000' # path for capture folder
number_images = 128  

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
        if '1000x1000' in scc.Resolution.AvailableValues or 'Custom...' in scc.Resolution.AvailableValues:
            scc.Resolution.Value = '1000x1000'
    # Reset 1000x1000 region of interest (ROI) to the center of the screen
    if scc.Pan.Available and scc.Tilt.Available:
        scc.Pan.Value = str(int(int(scc.Resolution.AvailableValues[0].Split('x')[0])/2-500))
        scc.Tilt.Value = str(int(int(scc.Resolution.AvailableValues[0].Split('x')[1])/2-500)) 

    ### Capture DARKS ####################################################################
    ss.CreateCameraSettingsFile = True
    x = scc.Exposure.ExposureMs
    for i in range(number_images):       
        sc.CaptureSingleFrameTo(str(capture_path / f'dark_{str_date}_{x}ms_{i+1}.fits'))
        ss.CreateCameraSettingsFile = False
    

    ### Reset SharpCap to live mode with appropriate exposure #############################  
    ss.CreateCameraSettingsFile = True 
    if sc.CanRunInLiveMode:
        sc.LiveView = True
    if scc.Resolution.Available:
        scc.Resolution.Value = reset_area 

# END OF PROGRAM
