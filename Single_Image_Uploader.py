import tkinter as tk 
from tkinter import filedialog
from tkinter import *
 
from pathlib import Path
'''
# Add this directory to python path
filedir = str(Path(__file__).parent)
if not filedir in sys.path:
    sys.path.append(filedir)
 '''   
import os
import subprocess
import datetime
import re

from deb_util import DebConfig

config = DebConfig()

folder = config.get('site_siu_folder')
rsa = config.get('site_siu_ssh_key')
upload_host = config.get('siu_upload_host')
my_id = Path(os.getenv('USERPROFILE', os.getenv('HOME'))) / '.ssh' / rsa
who_am_i = f'{folder}@{upload_host}'
batch = 'instruct.bat'
##########################################################################################################################

class uploader_window(tk.Tk):
    def __init__(self):
        super().__init__()
                
        self.geometry("300x100")
        self.title("Upload Image")
        self.configure(bg="black")
        self.header = tk.Label(self, text = 'Click the "Upload" button to select and upload an image')
        self.header.configure(bg="gray")
        self.header.place(relx=0.0, rely=0.0, relwidth=1.0, relheight=0.2)

def get_image():
    image.set(filedialog.askopenfilename(title = 'Select image to upload'))
    new_image = str(image.get())
    new_image = os.path.basename(new_image)
    new_image = new_image.replace(' ','_')
    str_sect = r'\d\d\d\d-\d\d-\d\d_\d\d\d\d\d\d'
    if not re.search(str_sect,new_image):
        time_insert = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d_%H%M%S')
        fname, ext = os.path.splitext(new_image)
        new_image = '{}_{}{}'.format(fname,time_insert,ext)
    commands = ['progress', 'put ' + '"' + image.get() + '" ' + new_image, 'bye'] #quotation marks meant to handle names with spaces included 

    file = open(batch,'w')
    for line in commands:
        file.write(line + "\n")
    file.close()
    
    args = ['sftp', '-i', my_id, '-b', batch, who_am_i]
    #for i in args: print(i)
    subprocess.call(args)
    os.remove(batch)


uploader = uploader_window()
image = tk.StringVar()

start_button = Button(uploader, text='Upload', command=lambda : get_image())
start_button.configure(bg="gray")
start_button.place(relx=0.4, rely=0.5)

uploader.mainloop()