# Monitors upload folder for new files to upload to debra.physics.siu.edu
# Creates .bat file for upload and executes it 
# deletes trigger and uploaded file after upload attempted



from pathlib import Path
import sys

# Add this directory to python path
filedir = str(Path(__file__).parent)
if not filedir in sys.path:
    sys.path.append(filedir)

import subprocess
import os
import glob
import time

from deb_util import DebConfig

config = DebConfig()

deb_path = Path(config.get('deb_path'))
upload_path = deb_path / 'Upload'
folder = config.get('site_siu_folder')
rsa = config.get('site_siu_ssh_key')
upload_host = config.get('siu_upload_host')


my_id = Path(os.getenv('USERPROFILE', os.getenv('HOME'))) / '.ssh' / rsa
who_am_i = f'{folder}@{upload_host}'

upload_dir = config.upload_dir()

# TODO for some reason Paths are not comparing correctly.
new = str(config.upload_workpath())
end = str(config.upload_endpath())
batch = r'C:\DEB\Programs\instruct.bat'

print(f'This program will monitor {upload_path} for new files and automatically upload them to {who_am_i}')

first = True # new variable to check if first run of code       
while True:
    files = [str(p) for p in upload_dir.glob('*.txt')] # look for new.txt and end.txt in Upload folder
    
    # Cleanup Upload folder to avoid unexpected behavior
    if first:
        if len(files) >=1:
            print("\nCleaned up Upload folder to avoid unexpected behavior\n")
            for file in files:
                os.remove(file)
        first = False
        continue
    
    ### check for new image and get name while protecting against race condition on new.txt
    if new in files:
        check_busy = 1
        while check_busy:
            try:
                with open(new, 'r') as f:
                    image = f.readline().strip()
                check_busy = 0
            except: 
                pass
        if not os.path.exists(image):
            print(f'Warning: {image} not found')
            continue
    
        ### build instruct.bat
        commands = ['progress', 'put ' + image, 'bye'] 
        file = open(batch,'w')
        for line in commands:
            file.write(line + "\n")
        file.close()
        
        ### call sftp 
        args = ['sftp', '-i', my_id, '-b', batch, who_am_i]    
        subprocess.call(args)
        
        ### clean up Upload
        os.remove(new) # remove new.txt so not uploading twice       
        if 'small' in image: # remove downsized images 
            os.remove(image)

    ### end program at end.txt signal
    if end in files:
        print('Terminating Program with correct signal')
        os.remove(end)
        time.sleep(1)
        break  

    #print(files)
    time.sleep(10) ### set to check every 10 seconds when not actively uploading
        
# End Program
