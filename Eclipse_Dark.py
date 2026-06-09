"""SharpCap IronPython script for dark calibration frames at max resolution
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

# Capture DARKS
# 64 count each exposure          
#
# Authors: Chris Mandrell, Castor Fu
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
capture_path = data_path / str_date / 'Darks_Full-Res' # path for capture folder
number_images = 64
exposure = ( 0.3, 0.4, 4.0, 40.0, 130.0, 400.0 ) # exposure tuple (ms)   

def main(SharpCap):
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
    
if __name__ == '__main__':
    main(SharpCap)

# END OF PROGRAM
