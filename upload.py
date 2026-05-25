# Monitors upload folder for new files to upload to debra.physics.siu.edu
# In standard mode (triggered by new.txt) uploads images and deletes downsized images if exists
# In totality mode (triggered by totality.txt)
#       collects most recent totality images
#       builds set of contiguous exposures from end of most recent images
#       tracks images so doesn't reprocess
#       creates HDR from contiguous set of exposures
#       downsizes HDR if set in config file 
#       uploads HDR
#       continues until end_totality.txt trigger or > 20sec of no new images
#       returns to monitoring mode
#
# Upload with sftp system call with .bat file created for each image
#
#

from pathlib import Path
import sys
import subprocess
import os
import glob
import time
import numpy as np
from  astropy.io import fits
import cv2 as cv
from PIL import Image,ImageEnhance

########## Build DEB Configuration ###########################################
from deb_util import DebConfig

# Add this directory to python path
filedir = str(Path(__file__).parent)
if not filedir in sys.path:
    sys.path.append(filedir)

config = DebConfig()

str_date = time.strftime("%Y-%m-%d",time.gmtime())
deb_path = Path(config.get('deb_path'))
upload_path = deb_path / 'Upload'
capture_path = deb_path / str_date / 'Totality'
folder = config.get('site_siu_folder')
rsa = config.get('site_siu_ssh_key')
upload_host = config.get('siu_upload_host')
down_size = config.getboolean('down_size') #downsize .png gpp images before upload?
down_size_percent = config.getint('down_size_percent') #percentage of original size if down_size True
programs_path = Path(config.get('deb_programs'))
batch = str(programs_path / 'instruct.bat')

my_id = Path(os.getenv('USERPROFILE', os.getenv('HOME'))) / '.ssh' / rsa
who_am_i = f'{folder}@{upload_host}'

upload_dir = config.upload_dir()

new = str(config.upload_workpath())
end = str(config.upload_endpath())
start_totality_trigger = str(upload_path / 'totality.txt')
end_totality_trigger = str(upload_path / 'end_totality.txt')

processed = [] # global processed images variable to prevent re-processing HDR

############## HDR Function #################################################
def merge_fits(fitsnames, outjpeg, exp_list, gamma=4.0):
    print('. . .Building HDR')
    exp_list = [i/1000 for i in exp_list]
    exposure_times = np.array(exp_list, dtype=np.float32)
    fitsnames.sort(key=lambda x:float(x.split('_')[-1][:3]))
    # These are the magic numbers.  
    kernel = np.array([[-1,-1,-1], [-1,25,-1], [-1,-1,-1]])
    
    """Create an HDR jpeg from a list of fits files using OpenCV Debevec merge."""
    image_list = []
    for f in fitsnames:
        with fits.open(f) as hdul:
            primary = np.array(hdul[0].data)
            hdul.close()

        img_8bit = cv.normalize(primary, None, 0,255, cv.NORM_MINMAX,dtype=cv.CV_8U)
        if len(img_8bit.shape)==3 and img_8bit.shape[0]==3:
            cvin = np.moveaxis(img_8bit,0,-1)
        else:
            cvin = cv.cvtColor(img_8bit, cv.COLOR_GRAY2BGR)
        image_list.append(cvin)
    print('. . . . . .Successfully read .fits files')      
    merge_debevec = cv.createMergeDebevec()
    hdr_debevec = merge_debevec.process(image_list, times=exposure_times)
    tonemap1 = cv.createTonemap(gamma=gamma)
    res_debevec = tonemap1.process(hdr_debevec.copy())
    # Try simple sharpening: do this first to minimize ring at lunar limb
    sharpened = cv.filter2D(res_debevec, -1, kernel)
    sharpened_8bit = cv.normalize(sharpened, None, 0,255, cv.NORM_MINMAX, cv.CV_8U)
    cv.imwrite(outjpeg, sharpened_8bit)
    
    if not outjpeg.exists():
        print("ERROR: HDR failed!", args)
    else:
        print(". . . . . . . . .HDR Completed")
        
    if down_size:
        outjpeg = down_size_func(outjpeg, down_size_percent)
        
    upload(outjpeg)

def get_text_files():
    return [str(p) for p in upload_dir.glob('*.txt')]
      
def start_totality():
    exp_list = []
    get_data_list = [str(p) for p in capture_path.glob('*.fits')]
    for i in get_data_list:
        exp = i.split('_')[-1][:-7] 
        exp_list.append(exp)
    exp_list = list(set(exp_list))
    exp_list_length = len(exp_list)
    exp_list_sorted = sorted(exp_list, key = lambda x: float(x))
    print("HDR's will be created with {} exposures: {}".format(exp_list_length,exp_list_sorted))
    if exp_list_sorted:
        totality(exp_list_sorted, exp_list_length)
    else:
        try:
            os.remove(start_totality_trigger)
            monitor()
        except:
            print("Couldn't make exposure list, and can't find start totality trigger")
            monitor()
        
def totality(exp_list, exp_count):
    global processed
    check_point = 2*exp_count-1
    check_point_issue = False
    while True:

        flist = [str(p) for p in capture_path.glob('*.fits')]
        #flist = sorted(glob.glob(str(capture_path / '*.fits')), key=os.path.getctime)
        process_list = list(set(flist) - set(processed))
    
        ### Check sufficient images created and return to regular monitoring
        ###     if > 10 seconds without sufficient images (2*#exposures - 1)
        ###         totality.py creates new Totality trigger after each iteration
        ###             so program will return to Totality mode if required
        #print('list length: {}, check_point: {}'.format(len(process_list), check_point))
        if len(process_list) < check_point:
            if not check_point_issue:
                check_point_issue = True
                check_point_start_time = time.time()
            issue_elapsed_time = time.time() - check_point_start_time
            if issue_elapsed_time > 10.0:
                print('Totality timed out and is returning to monitor mode')
                if start_totality_trigger in get_text_files():
                    try:
                        os.remove(start_totality_trigger)
                        monitor()
                    except: 
                        monitor()
            continue
        check_point_issue = False 
        # End checking for # images and timing out 
        
        processed.extend(process_list)
        process_list_sorted = sorted(process_list)
        short_image_list = process_list_sorted[-1*(check_point+1):]
  
        ### Build image list of #exposures images for HDR with last (2*#exposures -1) images taken
        ### Sorting above could put 1st image of last set with previous set
        ### This method of building the list can fix this problem, but is not built
        ###     to be robust enough to 100% prevent the possibility of using a low exposure time image
        ###         from the previous set of images in the HDR
        
        hdr_image_list = [None]*exp_count
        first_filter = True
        for j in reversed(short_image_list): #start from end of image list
            if exp_list[-1] not in j and first_filter==True: #traverse reversed image list until find last exposure value
                continue
            first_filter = False
            for i, value in enumerate(exp_list): # iterate through exposure list for each image 
            
                if value in j and hdr_image_list[i]==None: # if image at exposure not filled in do that now
                    if i == 0 and (j.split('_')[2] == hdr_image_list[-1].split('_')[2]): #unless time on shortest exposure matches time on longest
                        continue
                    hdr_image_list[i] = j 
        
        print("HDR will be created with:")
        for h in hdr_image_list:
            print(h)
        ### If something goes wrong with building an image list for the HDR just move on to the next sets of images
        ### This might occur if multiple occurrences of SharpCap dropping the same exposure during capture 
        ###     I don't want to mess with anything during totality capture, so we will just go with it for now
        if None in hdr_image_list:
            print('Incomplete image list created. . .retrying')
            continue
        
        outjpeg_start = Path(hdr_image_list[-1])
        outjpeg_path = upload_path / ('HDR_'+outjpeg_start.with_suffix('.jpg').name)

        merge_fits(hdr_image_list, outjpeg_path, [float(i) for i in exp_list])
        
        ### Just checking to see if we should continue in Totality mode or return to monitor mode
        if end_totality_trigger in get_text_files():
            try:
                os.remove(end_totality_trigger)
                os.remove(start_totality_trigger)
                monitor()
            except: 
                monitor()
                
def down_size_func(image_path, scale_percent):
    
    print('reading image in down-size')
    img = cv.imread(str(image_path))
    print('changing image name in down-size')
    image_path = Path(image_path)
    image_path = str(image_path.with_name(image_path.stem + '_small.jpg'))
    print('writing new image in down-size')
    cv.imwrite(image_path, img, [int(cv.IMWRITE_JPEG_QUALITY), scale_percent])
    return image_path
    
def upload(image):
    print('Beginning upload process')
    if not os.path.exists(image):
        print(f'Warning: {image} not found')
        return
    
    print('building batch file')
    ### build instruct.bat
    commands = ['progress', 'put ' + str(image), 'bye'] 
    file = open(batch,'w')
    for line in commands:
        file.write(line + "\n")
    file.close()
    
    print('calling sftp')
    ### call sftp 
    #args = ['sftp', '-o', 'ConnectTimeout=2', '-i', my_id, '-b', batch, who_am_i]
    args = ['sftp', '-o', 'ConnectTimeout=2', '-b', batch, 'DEB_server']
    subprocess.call(args)
    
    ### clean up Upload      
    if 'small' in str(image): # remove downsized images 
        try:
            os.remove(str(image))
        except:
            print('Could not remove {}'.format(image))
            pass
        
    #monitor()
    
def monitor(first = False):
    print("In monitor mode")
    while True:
        files = get_text_files() # look for new.txt, totality.txt and end_totality in Upload folder
        
        # Cleanup Upload folder to avoid unexpected behavior
        if first:
            for i,name in enumerate(files):
                if "new.txt" in name or "end_totality.txt" in name:
                    os.remove(name)
            print("\nCleaned up Upload folder to avoid unexpected behavior\n")
            first = False
            continue
        
        if new in files:
            try:
                with open(new, 'r') as f:
                    image = f.readline().strip()
            except:
                print('Error: Unable to read {}'.format(new))
                continue
            try:
                os.remove(new)
            except:
                print('Unable to access {} to remove'.format(new))
                continue
            try:
                if down_size:
                    image = down_size_func(image, down_size_percent)
            except:
                print('Downsize failed!')
                continue
            try:
                
                upload(str(image))
            except:
                print('Upload failed!')
                continue

        if start_totality_trigger in files:
            print('start totality mode')
            start_totality()
        if end_totality_trigger in files:
            print('end totality mode with end totality trigger')
            try:
                os.remove(start_totality_trigger)
            except:
                pass
            try:
                os.remove(end_totality_trigger)
            except:
                pass
                           
        ### end program at end.txt signal removed but kept the function in case wants to be
        ### used at a later date
        if end in files:
            print('Terminating Program with correct signal')
            os.remove(end)
            time.sleep(1)
            break  

        time.sleep(10) ### set to check every 10 seconds when not actively uploading
                                    
def main():
    print(f'This program will monitor {upload_path} for new files and automatically upload them to {who_am_i}')

    first_pass = True #variable to check if first run of code       
    monitor(first_pass)

if __name__ == '__main__':
    main()

# End Program
