"""use gui to select and upload image to server
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
Utilizes GUI to let user select file easily for upload and sharing 
Requires ssh config format
Author: Chris Mandrell
"""
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
    
    args = ['sftp', '-b', batch, 'DEB_server']
    subprocess.call(args)
    os.remove(batch)
    
uploader = uploader_window()
image = tk.StringVar()

start_button = Button(uploader, text='Upload', command=lambda : get_image())
start_button.configure(bg="gray")
start_button.place(relx=0.4, rely=0.5)

uploader.mainloop()