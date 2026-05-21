More specific explanations of the code (original code for 2023/2024 eclipses and daily observations) than that 
provided here is available at: Mandrell C., et al, The Dynamic Eclipse Broadcast Initiative Software Development 
for Data Collection, Processing and Uploading During the 2024 April 8th, Total Solar Eclipse, 2025, PASP, 137, 
125007, https://doi.org/10.1088/1538-3873/ae24ad

The Dynamic Eclipse Broadcast (DEB) Initiative is a multiphase NASA and NSF funded heliophysics project
developed by Matt Penn and Bob Baer at Southern Illinois University - Carbondale (SIUC).

DEB utilizes citizen scientist networks to study the Sun's lower corona during total solar eclipses
and photosphere during daily solar observations with white-light solar photography methods to further our
understanding of plasma dynamics associated with coronal acceleration in the corona and X-flare evolution
on the photosphere.

For more imformation about DEB (including how to join the team): https://debinitiative.org/
For images of recent DEB observations: https://debra.physics.siu.edu/

DEB uses propietary SharpCap software for image capture and open-source Planetary System Stacker for image
processing. Images are downsized and uploaded to the DEB server for sharing with the public and as realtime
feedback for volunteer observers.

The code in this repository is used by DEB teams for all of their observations and processing. It
incorporates the IronPython scripting functionality of SharpCap with the Python processing required for 
PSS correction, HDR processing, and image down-sizing and uploading.

Specific details about the code can be found in the cited paper at the top of this page and in the program 
details at the bottom of this page.

Use of PSS requires Windows <= 3.8 and other dependancies not compatable with some of the DEB image processing
For this reason, DEB computers now run 2 versions of Python (3.8 and >=3.13)

Generally,

Eclipse observation scripts include partial, totality, and calibration frame collection routines. PSS sharpening, 
image downsizing, and automated uploading are available options for the partial and totality observations, with 
totality including an option for quick HDR creation.

Daily observation scripts include 4 photosphere routines to maximize group observation of the Sun without overly
stressing computational resources. PSS sharpening, image downsizing, and automated uploading are also options for 
these routines.

Specifically,

Totality.py : continuously collects series of .fits at preset exposures at full resolution 
Partial_Eclipse.py : captures 15s .ser video at 1000x1000 resolution at user selected exposure on 1 minute cadence
Eclipse_Flat/Dark.py : 2 calibrations scripts that capture flats/darks (.fits) for totality exposures/resolution
Daily_Observation-Xxx.py : 4 capture scripts that collect 15s sets of .fits images at 1000x1000 resolution with user 
	exposure on 1 minute cadence. Xxx determines "quarter" of the minute that 15s imageing occurs
Daily_Flat/Dark.py : 2 calibration scripts that capture flats/darks (.fits) for daily script exposure/resolution
Startup.py : initializes SharpCap camera and a few DEB specific settings
upload.py : upload and processing script specific to DEB - handles HDR creation, image down-sizing and automated uploading
pss_console.py : edited version of planetary system stacker pss_console.py to allow command line post-processing
deb_config.pss : generalized PSS configuration for automated post-processing
deb_util.py : initializes and provides interface for DEB configuration 
configparser.py : Standard Python configparser module from Python >= 3.12 to augment Python 3.8 version
Search-Upload_Flare_Data.py and Single_Image_Uploader.py are DEB specific uploading scripts for different phases of 
	the experiment