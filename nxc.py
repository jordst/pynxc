from tkinter import *
import ffmpeg
import platform
import sys
import os
import subprocess
from tkinter import filedialog
from tkinter import ttk
from ttkthemes import ThemedTk

def handle_focus_in(element):
    element.place_forget()

def handle_focus_out(entry, label):
    if len(entry.get()) == 0:
        wx, wy = float(entry.place_info()["x"])+5, float(entry.place_info()["y"])+5
        label.place(x=wx, y=wy)

def widget_binds(widgets):
    for i in range(0, len(widgets)):
        if 'entry' in str(widgets[i]):
            curr_entry = widgets[i]
            curr_label = widgets[i+1]
            curr_entry.bind("<FocusIn>", lambda event,\
                            curr_label=curr_label: handle_focus_in(curr_label))
            curr_entry.bind("<FocusOut>", lambda event,\
                            curr_entry=curr_entry,curr_label=curr_label:\
                            handle_focus_out(curr_entry, curr_label))

def slider_changed(bandLabel, valueName):
    bandLabel.configure(text=valueName.get())

def browse(option):
        filename[option] = filedialog.askopenfilename( title = "Select a File",
                                            filetypes = (("all files",
                                                            "*.*"),
                                                        ("all files",
                                                            "*.*")))
        label_file_explorer.configure(text="File: "+filename[option])

def close():
    window.destroy()

def shellCmd(path, cover_file, afilters, newfile, type_run):
    if type_run == "start":
        shell_cmd = ["ffmpeg", "-loglevel", "error", "-i", path ]

        if afilters.find('afir') > -1:
            ir_file = combo.get()
            shell_cmd += ["-i", "./reverb-files/"+ir_file]

        if applyCover.get() == 1:
            shell_cmd += ["-i", cover_file, "-map", "0:0", "-map", "1:0"]

        shell_cmd += [ "-y", "-filter_complex", afilters]

        if stripVid.get() == 1:
            shell_cmd += ["-vn"]

        shell_cmd += [newfile]
    else:
        shell_cmd = [
            "ffplay",
            "-af", afilters,
            "-x", "500",
            "-y", "500",
            "-showmode", "1",
            "-autoexit", path]

    print(shell_cmd)

    process = subprocess.Popen(shell_cmd, shell=False,\
                               stdout=subprocess.DEVNULL,\
                               stderr=subprocess.DEVNULL)

    if type_run == "start":
        stdout, stderr = process.communicate()
#        when this was after the process, no cmd window was opened as well 
        if process.returncode == 0:
            label_status.configure(text="+:"+newfile, foreground="green")
        elif process.returncode != 0:
            label_status.configure(text="Failed  -> "+path, foreground="red")
    return

def searchList(mylist, search):
    for f in mylist:
        if search in f:
            mylist.remove(f)
    return mylist

def runCmd(type_run):
    local_filename = filename["filename"]
    cover_file = filename["cover_file"]
    filestream = ffmpeg.probe(local_filename)
    audio_stream = next((stream for stream in filestream['streams']\
            if stream['codec_type'] == 'audio'), None)
    arate=(audio_stream["sample_rate"])

    extension_pos = int(local_filename.rindex("."))
    extension = local_filename[extension_pos:]
    song_pos = int(local_filename.rindex("/"))
    song = local_filename[song_pos+1:extension_pos]
    path = local_filename[:song_pos+1]

    filter_list = []
    final_filter = ""

    if float(speed_entry.get()) < 1.0:
        speed_type = "[slowed]"
    elif float(speed_entry.get()) > 1.0:
        speed_type = "[nightcore]"
    else:
        speed_type = "[normalspeed]"

    new_file_name = path+song+speed_type+extension

    if type_run == "start":
        if len(reverb_dry.get()) > 0:
            final_filter = "[0] [1] "
        else:
            final_filter = "[0] "

    if len(reverb_dry.get()) > 0 and len(reverb_wet.get()) > 0 and \
       len(reverb_level.get()) > 0:
        filter_list.append("afir=dry="+reverb_dry.get()+ \
                           ":wet="+reverb_wet.get()+ \
                           ":length="+reverb_level.get())

    if len(speed_entry.get()) > 0:
        filter_list.append("aresample="+arate+":\
        resampler=soxr:\
        dither_method=triangular:\
        precision=28:\
        matrix_encoding=dolby,\
        asetrate="+arate+"*"+speed_entry.get())

    if len(tempo_entry.get()) > 0:
        filter_list.append("atempo="+tempo_entry.get())

    if len(crusher_sample_entry.get()) > 0 and len(crusher_bits_entry.get()) > 0:
        filter_list.append("acrusher=samples="+crusher_sample_entry.get()+\
                           ":bits="+crusher_bits_entry.get())

    if len(echo_overall_volume.get()) > 0 and len(echo_volume.get()) > 0 and \
        len(echo_delay.get()) > 0 and len(echo_decay.get()) > 0:
            filter_list.append("aecho="+echo_overall_volume.get()+":"\
                               +echo_volume.get()+":"\
                               +echo_delay.get()+":"\
                               +echo_decay.get())

    if len(volume_entry.get()) > 0:
        filter_list.append("volume="+volume_entry.get())
    else:
        filter_list.append("volume=1")

    if band1_value.get() != 0:
        filter_list.append("equalizer=f=60:t=h:w=100:g="+str(band1_value.get()))
    if band2_value.get() != 0:
        filter_list.append("equalizer=f=230:t=h:w=200:g="+str(band2_value.get()))
    if band3_value.get() != 0:
        filter_list.append("equalizer=f=910:t=h:w=300:g="+str(band3_value.get()))
    if band4_value.get() != 0:
        filter_list.append("equalizer=f=4:t=k:w=500:g="+str(band4_value.get()))
    if band5_value.get() != 0:
        filter_list.append("equalizer=f=14:t=k:w=500:g="+str(band5_value.get()))

    if len(filter_list) > 1:
        if len(filter_entry.get()) > 0:
            filter_list.append(filter_entry.get())
    else:
        filter_list.append(filter_entry.get())

    final_filter += ','.join(filter_list)

    if len(reverb_dry.get()) > 0:
        final_filter += " [reverb]; " # finishing the first filters mix
    
    if type_run == "start": # reapply the filters to the second mix without reverb
        if len(reverb_dry.get()) > 0:
            final_filter += "[0] "
            filter_list = searchList(filter_list, 'afir')
            final_filter += ','.join(filter_list)
            final_filter += " [nonrvb];"
            final_filter += "[nonrvb] [reverb] amix=inputs=2:weights="+mix_weight.get()+" 1"
            # mixing both reverb and non-reverb versions into one

    if type_run == "preview":
        shellCmd(local_filename, cover_file, final_filter, new_file_name, type_run)
    elif type_run == "start":
        shellCmd(local_filename, cover_file, final_filter, new_file_name, type_run)
    return

# init
window = Tk()
window.tk.call("source", "azure.tcl")
window.tk.call("set_theme", "dark")
window.title('NxC')
window.geometry("960x530")
p1 = PhotoImage(file = 'icon.png')
window.iconphoto(False, p1)
stripVid = IntVar()
applyCover = IntVar()
retainTempo = IntVar()
filename=None
filename = { "filename" : None, "cover_file" : None}
band1_value = IntVar()
band2_value = IntVar()
band3_value = IntVar()
band4_value = IntVar()
band5_value = IntVar()
sliderup="+10"
sliderdown="-10"

# widgets
label_file_explorer = ttk.Label(window,
                        text = "Select a File to NxC",
                        width = 100,
                        wraplength=700)

label_status = ttk.Label(window,
                        text = "",
                        width = 100,
                        wraplength=700)

button_explore = ttk.Button(window,
                        text = "Browse Files",
                            command = lambda: [ browse("filename") ])

button_select_cover = ttk.Button(window,
                        text = "Choose Cover",
                            command = lambda: [ browse("cover_file") ])

button_exit = ttk.Button(window,
                        text = "Exit",
                        command = close)

button_preview = ttk.Button(window,
                        text = "Preview",
                        command = lambda: [ runCmd("preview") ])

button_start = ttk.Button(window,
                        text = "Start",
                        command = lambda: [ runCmd("start") ])

strip_vid_button = ttk.Checkbutton(window,
                        text="Remove Video?",
                        variable=stripVid,
                        onvalue=1,
                        offvalue=0)

apply_cover_button = ttk.Checkbutton(window,
                        text="Apply Cover?",
                        variable=applyCover,
                        onvalue=1,
                        offvalue=0)


speed_entry = ttk.Entry(window)
speed_label = ttk.Label(window, text = "Pitch")
speed_entry.insert(END,"1")

reverb_entry = ttk.Entry(window)

volume_entry = ttk.Entry(window)
volume_label = ttk.Label(window, text = "Volume")
volume_default_label = ttk.Label(window, text = "1", foreground="grey")
#volume_entry.insert(END,"1")

filter_entry = ttk.Entry(window)
filter_label = ttk.Label(window, text = "Custom Filter")
filter_default_label = ttk.Label(window, text = "...", foreground="grey")

tempo_entry = ttk.Entry(window)
tempo_label = ttk.Label(window, text = "Tempo")
tempo_default_label = ttk.Label(window, text = "1", foreground="grey")

reverb_dry = ttk.Entry(window)
reverb_dry_label = ttk.Label(window, text = "Reverb Dry")
reverb_dry_default_label = ttk.Label(window, text = "10", foreground="grey")

reverb_wet = ttk.Entry(window)
reverb_wet_label = ttk.Label(window, text = "Reverb Wet")
reverb_wet_default_label = ttk.Label(window, text = "10", foreground="grey")

reverb_level = ttk.Entry(window)
reverb_level_label = ttk.Label(window, text = "Reverb Level")
reverb_level_default_label = ttk.Label(window, text = "1 (0-1)", foreground="grey")

reverb_ir_files = os.listdir("./reverb-files")
combo_label = ttk.Label(window, text = "Impuse Respose")
combo = ttk.Combobox(
    state="readonly",
    values=reverb_ir_files,
    width=35
)
combo.current(0)

mix_weight = ttk.Entry(window)
mix_weight_label = ttk.Label(window, text = "Mixing Weight")
mix_weight_default_label = ttk.Label(window, text = "2 (1-10)", foreground="grey")

echo_overall_volume = ttk.Entry(window)
echo_overall_volume_label = ttk.Label(window, text = "Echo Full Volume")
echo_overall_volume_default_label = ttk.Label(window, text = "0-1 (1)", foreground="grey")

echo_volume = ttk.Entry(window)
echo_volume_label = ttk.Label(window, text = "Echo Volume")
echo_volume_label_default = ttk.Label(window, text = "0-1 (0.7)", foreground="grey")

echo_delay = ttk.Entry(window)
echo_delay_label = ttk.Label(window, text = "Echo Delay (ms)")
echo_delay_label_default = ttk.Label(window, text = "0-50", foreground="grey")

echo_decay = ttk.Entry(window)
echo_decay_label = ttk.Label(window, text = "Echo Decay")
echo_decay_label_default = ttk.Label(window, text = "0-1 (0.5)", foreground="grey")

crusher_sample_entry = ttk.Entry(window)
c_sample_label = ttk.Label(window, text = "Crusher Sample")
c_sample_default_label = ttk.Label(window, text = "0-100 (5-10)", foreground="grey")

crusher_bits_entry = ttk.Entry(window)
c_bits_label = ttk.Label(window, text = "Crusher Bits")
c_bits_default_label = ttk.Label(window, text = "(8)", foreground="grey")

band1_label = ttk.Label( window, text='60Hz')
band1_val_label = ttk.Label( window, text='0')
band2_label = ttk.Label( window, text='230Hz')
band2_val_label = ttk.Label( window, text='0')
band3_label = ttk.Label( window, text='910Hz')
band3_val_label = ttk.Label( window, text='0')
band4_label = ttk.Label( window, text='4kHz')
band4_val_label = ttk.Label( window, text='0')
band5_label = ttk.Label( window, text='14kHz')
band5_val_label = ttk.Label( window, text='0')

band1 = ttk.Scale(
    window,
    from_=int(sliderup),
    to=int(sliderdown),
    orient='vertical',
    command = lambda event: slider_changed(band1_val_label, band1_value),
    variable=band1_value)

band2 = ttk.Scale(
    window,
    from_=int(sliderup),
    to=int(sliderdown),
    orient='vertical',
    command = lambda event: slider_changed(band2_val_label, band2_value),
    variable=band2_value)

band3 = ttk.Scale(
    window,
    from_=int(sliderup),
    to=int(sliderdown),
    orient='vertical',
    command = lambda event: slider_changed(band3_val_label, band3_value),
    variable=band3_value)

band4 = ttk.Scale(
    window,
    from_=int(sliderup),
    to=int(sliderdown),
    orient='vertical',
    command = lambda event: slider_changed(band4_val_label, band4_value),
    variable=band4_value)

band5 = ttk.Scale(
    window,
    from_=int(sliderup),
    to=int(sliderdown),
    orient='vertical',
    command = lambda event: slider_changed(band5_val_label, band5_value),
    variable=band5_value)


widget_list = [
        crusher_sample_entry,
        c_sample_default_label,
        crusher_bits_entry,
        c_bits_default_label,
        echo_overall_volume,
        echo_overall_volume_default_label,
        echo_volume,
        echo_volume_label_default,
        echo_delay,
        echo_delay_label_default,
        echo_decay,
        echo_decay_label_default,
        tempo_entry,
        tempo_default_label,
        volume_entry,
        volume_default_label,
        filter_entry,
        filter_default_label,
        reverb_dry,
        reverb_dry_default_label,
        reverb_wet,
        reverb_wet_default_label,
        reverb_level,
        reverb_level_default_label,
        mix_weight,
        mix_weight_default_label
        ]

widget_binds_list = widget_binds(widget_list)

# positions
label_file_explorer.place(x=120, y=15)
button_explore.place(x=10,y=10)
button_preview.place(x=15, y=470)
button_start.place(x=120, y=470)
button_select_cover.place(x=380,y=470)
button_exit.place(x=805, y=470)
label_status.place(x=0, y=435)
strip_vid_button.place(x=225, y=473)
apply_cover_button.place(x=490, y=473)

band1.place(x=105, y=305)
band1_label.place(x=107, y=285)
band1_val_label.place(x=109, y=405)

band2.place(x=157, y=305)
band2_label.place(x=159, y=285)
band2_val_label.place(x=161, y=405)

band3.place(x=211, y=305)
band3_label.place(x=213, y=285)
band3_val_label.place(x=215, y=405)

band4.place(x=265, y=305)
band4_label.place(x=267, y=285)
band4_val_label.place(x=269, y=405)

band5.place(x=315, y=305)
band5_label.place(x=317, y=285)
band5_val_label.place(x=319, y=405)

speed_entry.place(x=120, y=80)
speed_label.place(x=20, y=85)

tempo_entry.place(x=120, y=120)
tempo_label.place(x=20, y=125)
tempo_default_label.place(x=125, y=125)

crusher_sample_entry.place(x=120, y=160)
c_sample_label.place(x=20, y=163)
c_sample_default_label.place(x=125, y=165)

crusher_bits_entry.place(x=120, y=200)
c_bits_label.place(x=20, y=203)
c_bits_default_label.place(x=125, y=205)

volume_entry.place(x=120, y=240)
volume_label.place(x=20, y=243)
volume_default_label.place(x=125, y=245)

echo_overall_volume.place(x=410, y=80)
echo_overall_volume_label.place(x=290, y=83)
echo_overall_volume_default_label.place(x=415, y=84)

echo_volume.place(x=410, y=120)
echo_volume_label.place(x=290, y=123)
echo_volume_label_default.place(x=415, y=124)

echo_delay.place(x=410, y=160)
echo_delay_label.place(x=290, y=163)
echo_delay_label_default.place(x=415, y=164)

echo_decay.place(x=410, y=200)
echo_decay_label.place(x=290, y=203)
echo_decay_label_default.place(x=415, y=205)

filter_entry.place(x=410, y=240)
filter_label.place(x=290, y=243)
filter_default_label.place(x=415, y=245)

combo.place(x=690, y=80) 
combo_label.place(x=590, y=80)

reverb_dry.place(x=690, y=120)
reverb_dry_label.place(x=590, y=123)
reverb_dry_default_label.place(x=695, y=123)

reverb_wet.place(x=690, y=160)
reverb_wet_label.place(x=590, y=163)
reverb_wet_default_label.place(x=695, y=163)

reverb_level.place(x=690, y=200)
reverb_level_label.place(x=590, y=203)
reverb_level_default_label.place(x=695, y=203)

mix_weight.place(x=690, y=243)
mix_weight_label.place(x=590, y=248)
mix_weight_default_label.place(x=700, y=248)

window.mainloop()
