# 12/6/2023
# Capture FLATS
# 128 count @ users set exposure          
#
# Camera in Still Mode for captures
# resets to Live mode with original resolution after run
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
capture_path = data_path / str_date / 'Flats' # path for capture folder
number_images = 128

if __name__ == '__main__':
#def main():

    s = SharpCap
    ss = s.Settings
    sc = s.SelectedCamera
    scc = sc.Controls

    ### Initial Setup ####################################################################
    sc = SharpCap.Cameras[0]
    sc.LiveView = False

    #reset values for returning to live mode at end of collection
    reset_area = scc.Resolution.Value
    exposure_value = scc.Exposure.ExposureMs
    #Forced values
    scc.Binning.Value = '1'
    scc.OutputFormat.Automatic = False
    scc.OutputFormat.Value = 'FITS files (*.fits)'
    scc.ColourSpace.Value = 'MONO16'
    scc.Resolution.Value = '1000x1000'
    # Reset 1000x1000 region of interest (ROI) to the center of the screen
    scc.Pan.Value = str(int(int(scc.Resolution.AvailableValues[0].Split('x')[0])/2-500))
    scc.Tilt.Value = str(int(int(scc.Resolution.AvailableValues[0].Split('x')[1])/2-500)) 

    ### Capture FLATS ####################################################################
    for i in range(number_images):       
        sc.CaptureSingleFrameTo(str(capture_path / f'flat_{str_date}_{exposure_value}ms_{i+1}.fits'))
        ss.CreateCameraSettingsFile = False

    ### Reset SharpCap to live mode with appropriate exposure #############################  
    ss.CreateCameraSettingsFile = True   
    sc.LiveView = True
    sc.Controls.Resolution.Value = reset_area   

# END OF PROGRAM
