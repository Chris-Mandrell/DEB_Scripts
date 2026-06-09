"""Search for flare data and upload from users computer
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
program to locate/copy/upload flare data from SharpCap capture folder 

Completed:
    Identify date/time
        i) from input file sent as argument (full path if not in same folder as program)
        ii) from user prompted input at runtime
    Iterate through multiple flares in input file
    Calculate for flare occuring over two UTC days
    Works with deb.ini
        runs from regular Programs folder listed in deb.ini 
                or 
        any folder with:
            deb_util.py
    Raw data out to new Flare_data_xxxx-xx-xx folder
    Prompt to enter flare_info.txt after starting
    Prompt for rclone uploading:
        yes: start rclone upload
        no : create .txt with rclone command that can be copy/paste ran from cmd
    get darks/flats
        
To Do:
    fix mkdir and file write issues
    Improve flats search to include +- 6 days
    Prompt for deletion of unwanted files? (NOT TO BE COMPLETED IN THIS VERSION!!!!!)      
Chris Mandrell, SIUC, DEB
written: 9/15/2024
"""
import tkinter as tk 
from tkinter import filedialog, ttk
from tkinter import *

from sys import exit
import glob 
import re 
from pathlib import Path
import sys

# Add this directory to python path
filedir = str(Path(__file__).parent)
if not filedir in sys.path:
    sys.path.append(filedir)
    
import time
import os
import shutil
import subprocess
import os.path

from deb_util import DebConfig

config = DebConfig()
        
### find capture folder structure
str_date = time.strftime("%Y-%m-%d",time.gmtime())
programs_path = Path(config.get('deb_programs'))
data_path = config.data_path()
##########################################################################################################################

######################## GUI Class definition #########################################################################
class Flare(tk.Tk):
    def __init__(self):
        super().__init__()
                
        self.geometry("1000x750")
        self.title("Find Flare Data")
        
        self.description = tk.Frame(self, bg='darkgrey', highlightbackground="grey", highlightthickness=2)
        self.description.place(relx=0.0, rely=0.0, relwidth=0.5, relheight=0.5)
        self.description.header = tk.Label(self.description, text='Description',font=("Arial",16,"bold"), bg='grey')
        self.description.header.place(relx=0.0, rely=0.0, relwidth = 1.0, relheight=0.1)
        self.description.body = tk.Frame(self.description, bg='darkgrey')
        self.description.body.place(relx=0.0, rely=0.1, relwidth=1.0, relheight=0.9)
               
        self.output = tk.Frame(self, bg='darkgrey', highlightbackground="grey", highlightthickness=2)
        self.output.place(relx=0.5, rely=0.5, relwidth=0.5, relheight=0.5)
        self.output.header = tk.Label(self.output, text='Output',font=("Arial",16,"bold"), bg='grey')
        self.output.header.place(relx=0.0, rely=0.0, relwidth=1.0, relheight=0.1)
        self.output.body = tk.Frame(self.output, bg='darkgrey')
        self.output.body.place(relx=0.0, rely=0.1, relwidth=1.0, relheight=0.9)
        
        self.record = tk.Frame(self, bg='darkgrey', highlightbackground="grey", highlightthickness=2)
        self.record.place(relx=0.0, rely=0.5, relwidth=0.5, relheight=0.5)
        self.record.header = tk.Label(self.record, text='Output Log',font=("Arial",16,"bold"), bg='grey')
        self.record.header.place(relx=0.0, rely=0.0, relwidth=1.0, relheight=0.1)
        self.record.body = tk.Frame(self.record, bg='darkgrey')
        self.record.body.place(relx=0.0, rely=0.1, relwidth=1.0, relheight=0.9)
        
        self.instruction = tk.Frame(self, bg='darkgrey', highlightbackground="grey", highlightthickness=2)
        self.instruction.place(relx=0.5, rely=0.0, relwidth=0.5, relheight=0.5)
        self.instruction.header = tk.Label(self.instruction, text='Instructions',font=("Arial",16,"bold"), bg='grey')
        self.instruction.header.place(relx=0.0, rely=0.0, relwidth=1.0, relheight=0.1)
        self.instruction.body = tk.Frame(self.instruction, bg='darkgrey')
        self.instruction.body.place(relx=0.0, rely=0.1, relwidth=1.0, relheight=0.9)
        
        self.instruction.body.second = tk.Frame(self.instruction, bg='darkgrey')
        
        self.final_log = tk.Frame(self, bg='darkgrey', highlightbackground="grey", highlightthickness=2)
        self.final_log.header = tk.Label(self.final_log, text='Final Configuration',font=("Arial",16,"bold"), bg='grey')
        self.final_log.body = tk.Frame(self.final_log, bg='darkgrey')
 
######################## GUI auxillary functions #########################################################################     
"""reset function must handle resetting from any stage of computation"""
def reset(box, select, select_instruct, select_output, select_record, continue_button, file_button, reset_button, folder_button):
    record_string.set(record_string.get() + '\n-----------------------------------------\n-----------------RESET-------------------\n-----------------------------------------\n')
    select_record.delete(1.0,END)              
    select_record.insert(INSERT, record_string.get())
    select_record.pack()
    file_button.config(bg=reset_button.cget('bg'))
    file_button.place_forget()
    folder_button.config(bg=reset_button.cget('bg'))
    folder_button.place_forget()
    info_path.set('')
    folder_path.set('')
    box.instruction.body.second.place_forget()
    box.final_log.place_forget()
    select_files(box, select, select_instruct, select_output, select_record, continue_button, file_button, reset_button, folder_button)

""" gets flare data file name/location while recording results in output and log windows """
def get_info_file(button, select_output, select_record, continue_button):
    filename = filedialog.askopenfilename(title = "Select the flare information text file")
    reader = open(filename,'r')
    file_contents = reader.read()
    reader.close()
    info_path.set(filename)
    new_string = '\nFlare information file:\n' + info_path.get() +'\n\nFile contents:\n'+file_contents+'\n'
    output_string.set(new_string)
    record_string.set(record_string.get() + new_string)
    select_output.delete(1.0,END)
    select_output.insert(INSERT, output_string.get())
    select_output.pack()
    select_record.delete(1.0,END)
    select_record.insert(INSERT, record_string.get())
    select_record.pack()
    button.config(bg='green')
    if len(info_path.get()) > 1 and len(folder_path.get()) > 1:
        continue_button.configure(state=NORMAL)
    else:
        continue_button.configure(state=DISABLED)

""" gets data folder name/location while recording information in output and log windows """    
def get_data_folder(button, select_output, select_record, continue_button):
    folder_path.set(filedialog.askdirectory(title = "Select the Main Data Folder"))
    new_string = '\nObservation data folder:\n' + folder_path.get() +'\n'
    output_string.set(new_string)
    record_string.set(record_string.get() + new_string)
    select_output.delete(1.0,END)
    select_output.insert(INSERT, output_string.get())
    select_output.pack()
    select_record.delete(1.0,END)
    select_record.insert(INSERT, record_string.get())
    select_record.pack()
    button.config(bg='green')
    if len(info_path.get()) > 1 and len(folder_path.get()) > 1:
        continue_button.configure(state=NORMAL)
    else:
        continue_button.configure(state=DISABLED)

""" function to process each flare instance in flare_info file """        
def get_values(f):
    start_date = f.readline().replace('/','-')
    if start_date == "ENDOFFILE" or start_date =="ENDOFFILE\n" or start_date == '' or start_date =='\n':
        return "","","",""
    start = f.readline()        
    end = f.readline()
    
    start_splice = start.split(':')
    end_splice = end.split(':')

    # check for flare over multiple days 
    if int(start_splice[0]) > int(end_splice[0]):
        end_date = start_date[:8]+str(int(start_date[8:])+1)
    else:
        end_date = start_date
        
    return start_date, start, end_date, end

""" search for all relavant files and calculate memory required - called by calc_func()"""    
def get_metadata(date_folder, start, end):
    file_count = 0
    file_size = 0
    nothing_file = True
    check_start = int(start.replace(':','')[0:4]) # just want hour & minutes for checking times
    check_end = int(end.replace(':','')[0:4]) # just want hour & minutes for checking times
    
    main_folder = glob.glob(str(folder_path.get())+r'\*') # initial search of data folder    
    for i in main_folder:
        if date_folder in i and 'Flare_data' not in i:          
            sub_folders = glob.glob(i+r'\*') # get sub-folders in correct date folder
            for j in sub_folders:                
                if 'Daily_Photosphere' in j:
                    fits_files = glob.glob(j+r'\*.fits') # get files in main data folder
                    
                    while check_start <= check_end:
                        #new_minute = True # keep track of groups of files per minute
                        for k in fits_files:                           
                            filename = os.path.split(k)[1]
                            filename_time = re.search('_[0-9][0-9]_[0-9][0-9]_[0-9][0-9]_',filename)
                            int_time_tot = int(filename_time.group().replace('_','')) # full file timestamp including seconds
                            int_time = int(filename_time.group().replace('_','')[0:4]) # hour + minutes file timestamp for comparison to flare time
                            
                            if int_time == check_start:
                                if nothing_file: 
                                    nothing_file = False
                                file_count+=1
                                file_size+=os.path.getsize(k)
                                #if new_minute: # need to separate images by minute for PSS images
                                    #new_minute = False
                        check_start+=1
                        
            if not nothing_file:
                dark_flat_count = 0
                dark_flat_size = 0
                for k in sub_folders:                               
                    if 'Darks' in k:
                        dark_files = glob.glob(k+r'\*')
                        for df in dark_files:
                            dark_flat_count+=1
                            dark_flat_size+=os.path.getsize(df)
                    if 'Flats' in k:
                        flat_files = glob.glob(k+r'\*')
                        for ff in flat_files:
                            dark_flat_count+=1
                            dark_flat_size+=os.path.getsize(ff)
                file_count+=dark_flat_count
                file_size+=dark_flat_size
                
                    
    return file_count, file_size

""" build individual rclone commands from user inputs """    
def get_rclone():
    if var_auto_sync.get()=='Yes':
        holder = 'AUTOMATED upload template: rclone sync'
    else:
        holder = 'MANUAL upload template: rclone sync'
        
    if var_verbose.get()=='Yes':
        holder += ' --progress'
        
    if var_blimit.get()=='Yes':
        holder += ' --bwlimit {}{}'.format(var_limit_value.get(), var_limit_factor.get())
        
    holder += ' {}/Flare_data_xxxx-xx-xx debra:Flare_data_xxxx-xx-xx'.format(folder_path.get())
    output_string.set('\n'+holder)
    return holder

""" main code for calculating memory usage - calls get_metadata() """    
def calc_funct():
    os.system('cls')
    print('\n\n----------------------------------\n')
    print('Calculating Memory Requirements')
    print('\nThis may take a few minutes.\n')
    f = open(info_path.get())
    available_memory=shutil.disk_usage(folder_path.get())[2]
    file_count, file_size = 0,0
    start_date, start, end_date, end = get_values(f)
    while start_date: # runs until get_values() determines end, and returns empty value for start_date       
        if start_date == end_date:
            print('Calculating for {}....\n'.format(start_date.replace('\n','')))
            file_count_1, file_size_1 = get_metadata(start_date.replace('\n',''), start, end)
            file_count+=file_count_1
            file_size+=file_size_1
        else: # handle flare over 2 UTC days case
            print('Calculating for {} - {}....\n'.format(start_date.replace('\n',''),end_date.replace('\n','')))
            file_count_1, file_size_1 = get_metadata(start_date, start, '23:59:00')
            file_count+=file_count_1
            file_size+=file_size_1
            file_count_2, file_size_2 = get_metadata(end_date, '00:01:00', end)
            file_count+=file_count_2
            file_size+=file_size_2

        start_date, start, end_date, end = get_values(f)
    f.close()
    if file_size >= available_memory:
        quit_function = tk.Tk()
        quit_function.geometry('450x150')
        quit_function.title('Insufficient Memory')
        q_button = tk.Button(quit_function, text='Quit', width=25, command=lambda : exit())
        q_button.pack()
        quit_function.mainloop()

    return available_memory, file_count, file_size

""" main function for doing actual processing """    
def move_process(date_folder, start, end, capture_folder):
    check_start = int(start.replace(':','')[0:4]) # just want hour & minutes for checking times
    check_end = int(end.replace(':','')[0:4]) # just want hour & minutes for checking times
    
    flare_folder = os.path.join(capture_folder, 'Flare_data_{}'.format(date_folder)) # new folder for results
    
    main_folder = glob.glob(str(capture_folder)+r'\*') # initial search of data folder 
    
    nothing_folder = True # no folder matching search yet
    nothing_file = True # no file matching search yet
    for i in main_folder:
        if date_folder in i and 'Flare_data' not in i:
            nothing_folder = False # found folder for search date
          
            sub_folders = glob.glob(i+r'\*') # get sub-folders in correct date folder
            dark,flat = '','' # indicator for whether darks flats found
            for j in sub_folders:
                
                
                if 'Darks' in j:
                    dark = j
                if 'Flats' in j:
                    flat = j
                    
              
                if 'Daily_Photosphere' in j:
                    fits_files = glob.glob(j+r'\*.fits') # get files in main data folder
                    
                    while check_start <= check_end:
                        new_minute = True # keep track of groups of files per minute
                        for k in fits_files:                           
                            filename = os.path.split(k)[1]
                            filename_time = re.search('_[0-9][0-9]_[0-9][0-9]_[0-9][0-9]_',filename)
                            int_time_tot = int(filename_time.group().replace('_','')) # full file timestamp including seconds
                            int_time = int(filename_time.group().replace('_','')[0:4]) # hour + minutes file timestamp for comparison to flare time
                            
                            if int_time == check_start:
                                if nothing_file: # create Flare_data_xxxx_xx_xx only if usable flare data detected
                                    try:
                                        os.mkdir(flare_folder)
                                    except:
                                        pass # this assumes only one folder necessary, if trying to remake must be copying original data. program will error out later
                                    nothing_file = False # only need to create folder once

                                if new_minute: # need to separate images by minute for PSS
                                    folder_path = os.path.join(flare_folder, 'photosphere_{}_{}'.format(date_folder,int_time_tot))
                                    os.mkdir(folder_path)
                                    new_minute = False # only do this once per minute
                                shutil.copyfile(k,os.path.join(folder_path,filename))

                        check_start+=1
            if not nothing_file:
                if dark:
                    shutil.copytree(dark, os.path.join(flare_folder,'Darks'))
                if flat:
                    shutil.copytree(flat, os.path.join(flare_folder,'Flats'))
                    
    return nothing_file, flare_folder

""" build os.process callable rclone command for automated uploading """
def setup_rclone(rclone_folder, rclone_commands_new):
    rclone_commands_new.append(rclone_folder)    
    rclone_commands_new.append('debra:{}'.format(os.path.split(rclone_folder)[1]))
    return rclone_commands_new

""" generic quit function that handles internally built error and shutdown messaging and behavior """    
def quit_funct(reason):
    print('\n-------------------------------------------------------------------------\n')
    print("Program shutting down...{}".format(reason))
    exit()
    
######################## GUI text messages #########################################################################
def start_description():
    Zaphod = 'This program is designed to search your DEB folders and find any Daily Solar Observation data corresponding to an X-class flare and prepare it for uploading.'
    Beeblebrox = 'FLATS & DARKS WARNING!!!!: This beta version only looks for flats and darks under the date of interest...\n\t--You should be taking Darks daily and Flats weekly'
    towel = 'This box will contain useful background while the "Instructions" pane will guide you through the steps.'
    return Zaphod + '\n\n' + Beeblebrox + '\n\n' + towel
    
def start_instructions():
    towel = 'Click on the "Start" button below to begin'
    return towel
    
def select_files_description():
    Arthur = 'In this section you will be prompted to input the locations of files necessary to run the program:\n\t1) The flare information file\n\t2) The Main data folder'
    Dent = 'The Main data folder contains the dated observations you have collected with SharpCap, and the folder names are the date of capture (e.g. C:/DEB)'
    Babel = 'DO NOT SELECT A SPECIFIC DAYS FOLDER!!! --- SELECT THE FOLDER THAT THE SPECIFIC DATED FOLDER IS IN!'
    Fish = 'You can reselect by hitting a button again, or simply hit "Reset" to begin from scratch'
    return Arthur + '\n' + Dent + '\n' + Babel + '\n\n' + Fish
    
def select_files_instructions():
    ultimate = '1) Click "Select Observation Data Folder" to load the main observation data folder'
    question = '2) Click "Select Flare Data File" to load the flare date/time information file'
    forty_two = '3) Click "Continue" to proceed to the next steps'
    return ultimate + '\n\n' + question + '\n\n' + forty_two
    
def calc_description():
    Ford = 'This section will calculate, approximately, how much memory will be used during the processing and determine if you have sufficient space to proceed'
    Prefect = 'You will be prompted to continue if you are comfortable with the numbers (shown in the "Output" section)'
    return Ford + '\n\n' + Prefect
    
def calc_instructions():
    Trillian = 'If you are comfortable with the available memory, select "Continue" after the calculation is complete'
    Astra = 'The program will close if insufficient memory available'
    Tricia = 'You should exit the program or start over with "Reset" if the output shows zero files to process'
    return Trillian + '\n\n' + Astra + '\n\n' + Tricia
    
def set_sync_description():
    Heart = 'The processing can take a long time, so we will setup rclone before we begin.\nYou will be prompted for multiple variable values that will determine how the rclone sync process works'
    Gold = 'You will also have to indicate if you want the rclone procedure to run automatically after the processing is completed'
    Marvin = 'If you choose not to run rclone, the commands will still be created and saved to a document for your reference when you do decide to run them, so you still need to pick the other settings to match your preferences'
    GPP = 'To learn more about limiting the upload speed go to this address: https://rclone.org/docs/#bwlimit-bandwidth-spec'
    return Heart + '\n\n' + Gold + '\n\n' + Marvin + '\n\n' + GPP
    
def set_sync_instructions():
    return

def final_instructions():
    towel = 'If you are happy with this final configuration select "Continue" to perform processing\n\tALL FURTHER INFORMATION DISPLAYED ON COMMAND PROMPT\n\nOtherwise select "Reset" or close program'
    return towel

######################## GUI main process functions #########################################################################
    
def introduction(box):    
    intro = tk.Text(box.description.body, width=500, wrap='word', bg='darkgrey')
    intro.insert(INSERT,start_description())
    intro.pack()
    intro_instruct = tk.Text(box.instruction.body, width=500, wrap='word', bg='darkgrey')
    intro_instruct.insert(INSERT, start_instructions())
    intro_instruct.pack()
    scroll_output = Scrollbar(box.output.body, orient='vertical')
    scroll_output.pack(side=RIGHT, fill='y')
    intro_output = tk.Text(box.output.body,width=500, wrap='word', bg='darkgrey')
    scroll_output.config(command=intro_output.yview)
    intro_output.pack()
    scroll_record = Scrollbar(box.record.body, orient='vertical')
    scroll_record.pack(side=RIGHT, fill='y')
    intro_record = tk.Text(box.record.body,width=500, wrap='word', bg='darkgrey')
    scroll_record.config(command=intro_record.yview)
    intro_record.pack()
    
    start_button = Button(box.instruction.body, text="Start", command=lambda : start_run(box, intro, intro_instruct, intro_output, intro_record, start_button, continue_button, file_button, reset_button, folder_button))
    start_button.place(relx=0.5, rely=0.2)
    continue_button = Button(box.instruction.body, text="Continue", state=DISABLED, command=lambda : calc_memory(box, intro, intro_instruct, intro_output, intro_record, continue_button, file_button, reset_button, folder_button))
    file_button = Button(box.instruction.body, text="Flare Data File", command=lambda : get_info_file(file_button, intro_output, intro_record, continue_button))
    folder_button = Button(box.instruction.body, text="Observation Data Folder", command=lambda : get_data_folder(folder_button, intro_output, intro_record, continue_button))
    reset_button = Button(box.instruction.body, text="Reset", command=lambda : reset(box, intro, intro_instruct, intro_output, intro_record, continue_button, file_button, reset_button, folder_button))

""" function necessary to destroy startup page to simplify resetting from other pages """       
def start_run(box, intro, intro_instruct, intro_output, intro_record, start_button, continue_button, file_button, reset_button, folder_button):
    start_button.destroy()
    select_files(box, intro, intro_instruct, intro_output, intro_record, continue_button, file_button, reset_button, folder_button)

""" collects flare info filename/location and main data folder """    
def select_files(box, select, select_instruct, select_output, select_record, continue_button, file_button, reset_button, folder_button):
    continue_button.config(state=DISABLED, command=lambda : calc_memory(box, select, select_instruct, select_output, select_record, continue_button, file_button, reset_button, folder_button))
    reset_button.configure( command=lambda : reset(box, select, select_instruct, select_output, select_record, continue_button, file_button, reset_button, folder_button))
    select_output.delete(1.0,END)
    
    select.delete(1.0,END)
    select_instruct.delete(1.0,END)
    
    select.insert(INSERT, select_files_description())
    select.pack()
    select_instruct.insert(INSERT, select_files_instructions())
    select_instruct.pack()
    
    continue_button.place(relx=0.25,rely=0.9)
    file_button.place(relx=0.7, rely=0.5)
    folder_button.place(relx=0.1, rely=0.5)
    reset_button.place(relx=0.0, rely=0.9)

""" handle appearance and function call for required memory calculations """              
def calc_memory(box, calc, calc_instruct, calc_output, calc_record, continue_button, file_button, reset_button, folder_button):
    box.withdraw()
    calc.delete(1.0,END)
    calc_instruct.delete(1.0,END)
    file_button.place_forget()
    folder_button.place_forget()
    continue_button.configure(state=DISABLED, command=lambda : config_rclone(box, calc, calc_instruct, calc_output, calc_record, continue_button, file_button, reset_button, folder_button))
    reset_button.configure( command=lambda : reset(box, calc, calc_instruct, calc_output, calc_record, continue_button, file_button, reset_button, folder_button))
    calc.insert(INSERT, calc_description())
    calc.pack()
    calc_instruct.insert(INSERT, calc_instructions())
    calc_instruct.pack()
    
    
    available_memory, file_count, file_size = calc_funct()  
    
    var_counter.set(file_count)
    new_string = '\nNew Data Memory Usage (Approximate):\n----------------------\nNumber of new files: {}\n           Available Memory:{: >18,} Bytes\nApproximate Memory required:{: >18,} Bytes\n'.format(file_count, available_memory, file_size)
    output_string.set(new_string)
    record_string.set(record_string.get()+'\n'+new_string)
    calc_output.delete(1.0,END)
    calc_output.insert(INSERT, output_string.get())
    calc_output.pack()
    calc_record.delete(1.0,END)
    calc_record.insert(INSERT, record_string.get())
    calc_record.pack()   
    
    continue_button.configure(state=NORMAL)
    box.update()
    box.deiconify()

""" collects rclone configuration from user inputs or defaults """    
def config_rclone(box, set_sync, set_sync_instruct, set_sync_output, set_sync_record, continue_button, file_button, reset_button, folder_button):
    file_button.place_forget()
    folder_button.place_forget()
    box.instruction.body.second.place(relx=0.0, rely=0.1, relwidth=1.0, relheight=0.9)
    set_sync.delete(1.0,END)  
    set_sync.insert(INSERT, set_sync_description())
    set_sync.pack()
    set_sync_instruct.delete(1.0,END)
    set_sync_output.delete(1.0,END)    
    
    # toggling between settings for --bwlimit
    def switch(*args):    
        if var_blimit.get()=='Yes':
            label_limit.grid(column=1, row=3, sticky='e', **paddings)
            
            menu_num.grid(column=2, row=3, **paddings )
            menu_factor.grid(column=3, row=3, **paddings)
        else:
            label_limit.grid_remove()
            menu_num.grid_remove()
            menu_factor.grid_remove()
        
        set_sync_output.delete(1.0,END)
        set_sync_output.insert(INSERT,get_rclone())
        set_sync_output.pack()
            
    verbose = ('Yes', 'No')
    var_verbose.set(value=verbose[0])
    blimit = ('Yes','No')
    var_blimit.set(value=blimit[1])
    #put typed entry box here
    auto_sync = ('Yes', 'No')
    var_auto_sync.set(value=auto_sync[0])
    num = ('5','10','15','20','25','30','40','45','50')
    var_limit_value.set(value=num[0])
    factor = ('B','K','M','G','T','P')
    var_limit_factor.set(value='M')
    get_rclone()
    set_sync_output.insert(INSERT,get_rclone())
    set_sync_output.pack()   
    paddings = {'padx':5, 'pady':5}
    
    label_verbose = tk.Label(box.instruction.body.second, text='Do you want to see the progress?')
    label_verbose.grid(column=0, row=1, sticky='e', **paddings)
    label_blimit = tk.Label(box.instruction.body.second, text='Do you want to limit the upload speed?')
    label_blimit.grid(column=0, row=2, sticky='e', **paddings)
    label_auto_sync = tk.Label(box.instruction.body.second, text='Do you want to run rclone automatically?')
    label_auto_sync.grid(column=0, row=0,sticky='e', **paddings)
    
    menu_verbose = tk.OptionMenu(box.instruction.body.second, var_verbose, *verbose)
    menu_verbose.grid(column=1, row=1, **paddings)
    menu_blimit = tk.OptionMenu(box.instruction.body.second, var_blimit, *blimit)
    menu_blimit.grid(column=1, row=2, **paddings)
    menu_auto_sync = tk.OptionMenu(box.instruction.body.second, var_auto_sync, *auto_sync)
    menu_auto_sync.grid(column=1, row=0, **paddings)
    
    label_limit = tk.Label(box.instruction.body.second, text='Select limit')
    menu_num = tk.OptionMenu(box.instruction.body.second, var_limit_value, *num)
    menu_factor = tk.OptionMenu(box.instruction.body.second, var_limit_factor, *factor)

    continue_button2 = Button(box.instruction.body.second, text="Continue", command=lambda : final_check(box, set_sync, set_sync_instruct, set_sync_output, set_sync_record, continue_button, file_button, reset_button, folder_button))
    reset_button2 = Button(box.instruction.body.second, text="Reset", command=lambda : reset(box, set_sync, set_sync_instruct, set_sync_output, set_sync_record, continue_button, file_button, reset_button, folder_button))
    continue_button2.place(relx=0.25,rely=0.9)
    reset_button2.place(relx=0.0, rely=0.9)
    var_blimit.trace('w',switch)
    var_verbose.trace('w',switch)
    var_auto_sync.trace('w',switch)
    var_limit_value.trace('w',switch)
    var_limit_factor.trace('w',switch)

""" prompt user to check final configuration before starting processing of data """
def final_check(box, final, final_instruct, final_output, final_record, continue_button, file_button, reset_button, folder_button): 
    final.delete(1.0,END)
    box.instruction.body.second.place_forget()    
    record_string.set(record_string.get() + output_string.get())
    final_output.delete(1.0,END)
    final_record.delete(1.0,END)
    box.final_log.place(relx=0.0, rely=0.0, relwidth=1.0, relheight=1.0)
    box.final_log.body.place(relx=0.0, rely=0.05, relwidth = 1.0, relheight=0.9)
    box.final_log.header.place(relx=0.0, rely=0.0, relwidth = 1.0, relheight=0.05)
    scroll = Scrollbar(box.final_log.body, orient='vertical')
    scroll.pack(side=RIGHT, fill='y')
    
    final_config = record_string.get().split('\n-----------------------------------------\n-----------------RESET-------------------\n-----------------------------------------\n')[-1]
    
    words = tk.Text(box.final_log.body, width=1000, height=990, wrap='word', bg='darkgrey')
    words.insert(INSERT,final_instructions()+'\n\n-------------------------Begin Final Config-------------------------'+final_config+'\n-------------------------End Final Config-------------------------')
    words.pack()                                  
    continue_button3 = Button(box.final_log.body, text="Continue", command=lambda : do_process(box, final, final_instruct, final_output, final_record, continue_button, file_button, reset_button, folder_button))
    reset_button3 = Button(box.final_log.body, text="Reset", command=lambda : reset(box, final, final_instruct, final_output, final_record, continue_button, file_button, reset_button, folder_button))
    continue_button3.place(relx=0.5, rely=0.05)
    reset_button3.place(relx=0.6, rely=0.05)

def do_process(box, final, final_instruct, final_output, final_record, continue_button, file_button, reset_button, folder_button):
    box.withdraw()
    
    os.system('cls')
    f = open(info_path.get())
    start_date, start, end_date, end = get_values(f)
    no_file_list = []
    flare_folder_list = [] # in case more than one flare date found
    while start_date: # runs until get_values() determines end, and returns empty value for start_date
        print("\nProcessing: {}, {} to {}".format(start_date.replace('\n',''), start.replace('\n',''), end.replace('\n','')))
        if start_date == end_date:
            no_file, flare_folder = move_process(start_date.replace('\n',''), start, end, folder_path.get())
            if not no_file:
                flare_folder_list.append(flare_folder)
            no_file_list.append(no_file)
        else: # handle flare over 2 UTC days case
            check1, flare_folder = move_process(start_date, start, '23:59:00', folder_path.get())
            if not check1: 
                flare_folder_list.append(flare_folder)
            check2, flare_folder = move_process(end_date, '00:01:00', end, folder_path.get())
            if not check2: 
                flare_folder_list.append(flare_folder)
            if not check1 or not check2:
                no_file = False
            else:
                no_file = True
            no_file_list.append(no_file)
        if not f: # breaks out of while loop if no input file provided and search was with user inputed date/times for single search
            break
        start_date, start, end_date, end = get_values(f)
        
    f.close()
    
    print('\n-------------------------------------------------------------------------\n')
    if False not in no_file_list: # successful completion with no flare data found
        quit_funct('There was no flare data found to process')       
    else: # continue to rclone process if successful completion with flare data identified               
        print('Processing complete. . .look for results in new {} folder(s)'.format(flare_folder_list))
        print('\n-------------------------------------------------------------------------')
        
        rclone_file = os.path.join(folder_path.get(),'rclone_commands_{}.txt'.format(str_date))
        f_clone = open(rclone_file,'w')
        f_clone.write('You can copy/paste these rclone commands at any command prompt\n')
        
        rclone_commands = ['rclone','sync']
        if var_verbose.get()=='Yes':
            rclone_commands.append('--progress')        
        if var_blimit.get()=='Yes':
            rclone_commands.append('--bwlimit')
            rclone_commands.append(var_limit_value.get()+var_limit_factor.get())
        rclone_event_list=[]
        for event in flare_folder_list:
            rclone_commands_new = rclone_commands.copy()
            rclone_event = setup_rclone(event, rclone_commands_new)
            rclone_event_list.append(rclone_event)
            rclone_cmd = ''
            for cmd in rclone_event:
                rclone_cmd += cmd
                rclone_cmd += ' '
            print('\nrclone command for {}:\n{}'.format(event,rclone_cmd))
            f_clone.write('\n'+rclone_cmd)
        f_clone.close()
        
        print('\n\nThe rclone command(s) have been saved to {}'.format(rclone_file))
                      
        if var_auto_sync.get()=='Yes':
            for instructions in rclone_event_list:
                status = subprocess.call(instructions)
                if status != 0:
                    print('There was an error running rclone:', status)
            
    quit_funct('\n\nOperation complete. . .all tasks completed successfully')       

    
######################## tkinter main #########################################################################   
# build main window
find_flare=Flare()
# set tkinter user input variables
info_path = tk.StringVar()
folder_path = tk.StringVar()
output_string = tk.StringVar()
record_string = tk.StringVar()
var_counter = tk.IntVar()
var_verbose = tk.StringVar()
var_blimit = tk.StringVar()
var_limit_value = tk.StringVar()
var_limit_factor = tk.StringVar()
var_auto_sync = tk.StringVar()

# start program with introduction() function
introduction(find_flare)
find_flare.mainloop()

### END OF FILE ###   