"""Collect flat calibration frames at daily observation resolution
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

"""
Capture flat calibration frames at daily observation resolution
128 frames
configured to force DEB camera values for:
resolution, pan, tilt, colourspace, binning
allows use of cameras without these available

Author: Chris Mandrell, Castor Fu
"""
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
capture_path = data_path / str_date / 'Flats_1000x1000' # path for capture folder
number_images = 128

def main(SharpCap):
    s = SharpCap
    ss = s.Settings
    sc = s.SelectedCamera
    scc = sc.Controls

    ### Initial Setup ####################################################################
    sc = SharpCap.Cameras[0]
    if sc.CanRunInLiveMode:
        sc.LiveView = False
    if scc.Resolution.Available:
        reset_area = scc.Resolution.Value 
    exposure_value = scc.Exposure.ExposureMs
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

    ### Capture FLATS ####################################################################
    for i in range(number_images):       
        sc.CaptureSingleFrameTo(str(capture_path / f'flat_{str_date}_{exposure_value}ms_{i+1}.fits'))
        ss.CreateCameraSettingsFile = False

    ### Reset SharpCap to live mode with appropriate exposure #############################  
    ss.CreateCameraSettingsFile = True   
    if sc.CanRunInLiveMode:
        sc.LiveView = True
    if scc.Resolution.Available:
        scc.Resolution.Value = reset_area
    
if __name__ == '__main__':
    main(SharpCap)    

# END OF PROGRAM
