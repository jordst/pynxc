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
                            handle_focus_out( curr_entry, curr_label))

def slider_changed(bandLabel, valueName):
    bandLabel.configure(text=valueName.get())

def browse():
    global filename
    filename = filedialog.askopenfilename( title = "Select a File",
                                          filetypes = (("all files",
                                                        "*.*"),
                                                       ("all files",
                                                        "*.*")))
    label_file_explorer.configure(text="File: "+filename)

def close():
    window.destroy()

def shellCmd(path, afilters, newfile, type_run):
    if type_run == "start":
        shell_cmd = [
            "ffmpeg",
            "-loglevel", "error",
            "-i", path,
            "-y",
            "-filter:a", afilters]

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

    process = subprocess.Popen(shell_cmd,\
            shell=True,
            stdout=subprocess.PIPE,\
            stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()

    if process.returncode == 0:
        if type_run == "start":
            label_status.configure(text="+:"+newfile, foreground="green")
        else:
            label_status.configure(text="+prev:"+path, foreground="green")
    elif process.returncode != 0:
        label_status.configure(text="Failed  -> "+path, foreground="red")
    return

def runCmd(type_run):
    filestream = ffmpeg.probe(filename)
    audio_stream = next((stream for stream in filestream['streams']\
            if stream['codec_type'] == 'audio'), None)
    arate=(audio_stream["sample_rate"])

    extension_pos = int(filename.rindex("."))
    extension = filename[extension_pos:]
    song_pos = int(filename.rindex("/"))
    song = filename[song_pos+1:extension_pos]
    path = filename[:song_pos+1]
    filters = ""

    volume_input = volume_entry.get()
    speed_input = speed_entry.get()
    tempo_input = tempo_entry.get()
    crusher_sample = crusher_sample_entry.get()
    crusher_bits = crusher_bits_entry.get()
    echo_o_vol = echo_overall_volume.get()
    echo_vol = echo_volume.get()
    echo_del = echo_delay.get()
    echo_dec = echo_decay.get()
    b1 = band1_value.get()
    b2 = band2_value.get()
    b3 = band3_value.get()
    b4 = band4_value.get()
    b5 = band5_value.get()

    if float(speed_input) < 1.0:
        speed_type = "[slowed]"
    elif float(speed_input) > 1.0:
        speed_type = "[nightcore]"
    else:
        speed_type = "[normalspeed]"

    new_file_name = path+song+speed_type+extension

    if len(speed_input) > 0:
        filters = "aresample=44100:resampler=soxr:dither_method=triangular:\
                precision=28:matrix_encoding=dolby,\
                asetrate="+arate+"*"+speed_input

    if len(tempo_input) > 0:
        filters += ",atempo="+tempo_input

    if len(crusher_sample) > 0 and len(crusher_bits) > 0:
        filters += ",acrusher=samples="+crusher_sample+":bits="+crusher_bits

    if len(echo_o_vol) > 0 and len(echo_vol) > 0 and \
        len(echo_del) > 0 and len(echo_dec) > 0:
            filters += ",aecho="+echo_o_vol+":"+echo_vol+":"+echo_del+":"+echo_dec

    if len(volume_input) > 0:
        filters += ",volume="+volume_input
    else:
        filters += ",volume=1"

    if b1 != 0:
        filters += ",equalizer=f=60:t=h:w=100:g="+str(b1)
    if b2 != 0:
        filters += ",equalizer=f=230:t=h:w=200:g="+str(b2)
    if b3 != 0:
        filters += ",equalizer=f=910:t=h:w=300:g="+str(b3)
    if b4 != 0:
        filters += ",equalizer=f=4:t=k:w=500:g="+str(b4)
    if b5 != 0:
        filters += ",equalizer=f=14:t=k:w=500:g="+str(b5)

    if type_run == "preview":
        filters += ",volume=0.5"
        shellCmd(filename, filters, new_file_name, type_run)
    elif type_run == "start":
        shellCmd(filename, filters, new_file_name, type_run)
    return

# init
window = Tk()
window.tk.call("source", "azure.tcl")
window.tk.call("set_theme", "dark")
window.title('NxC')
window.geometry("950x420")
p1 = PhotoImage(file = 'icon.png')
window.iconphoto(False, p1)
stripVid = IntVar()
retainTempo = IntVar()
filename=None
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
                        command = browse)

button_exit = ttk.Button(window,
                        text = "Exit",
                        command = close)

button_preview = ttk.Button(window,
                        text = "Preview",
                        command = lambda: [ runCmd("preview") ])

button_start = ttk.Button(window,
                        text = "start",
                        command = lambda: [ runCmd("start") ])

strip_vid_button = ttk.Checkbutton(window,
                        text="remove video?",
                        variable=stripVid,
                        onvalue=1,
                        offvalue=0)

speed_label = ttk.Label(window, text = "pitch")
speed_entry = ttk.Entry(window)
speed_entry.insert(END,"1.3")

volume_label = ttk.Label(window, text = "volume")
volume_entry = ttk.Entry(window)
volume_default_label = ttk.Label(window, text = "1", foreground="grey")
#volume_entry.insert(END,"1")

tempo_label = ttk.Label(window, text = "tempo")
tempo_entry = ttk.Entry(window)
tempo_default_label = ttk.Label(window, text = "", foreground="grey")

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
    variable=band1_value
)

band2 = ttk.Scale(
    window,
    from_=int(sliderup),
    to=int(sliderdown),
    orient='vertical',
    command = lambda event: slider_changed(band2_val_label, band2_value),
    variable=band2_value
)

band3 = ttk.Scale(
    window,
    from_=int(sliderup),
    to=int(sliderdown),
    orient='vertical',
    command = lambda event: slider_changed(band3_val_label, band3_value),
    variable=band3_value
)

band4 = ttk.Scale(
    window,
    from_=int(sliderup),
    to=int(sliderdown),
    orient='vertical',
    command = lambda event: slider_changed(band4_val_label, band4_value),
    variable=band4_value
)

band5 = ttk.Scale(
    window,
    from_=int(sliderup),
    to=int(sliderdown),
    orient='vertical',
    command = lambda event: slider_changed(band5_val_label, band5_value),
    variable=band5_value
)


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
        volume_default_label
        ]

widget_binds_list = widget_binds(widget_list)

# positions
label_file_explorer.place(x=120, y=15)
button_explore.place(x=10,y=10)
button_preview.place(x=15, y=330)
button_start.place(x=120, y=330)
button_exit.place(x=605, y=330)
label_status.place(x=0, y=275)
strip_vid_button.place(x=225, y=333)

band1.place(x=635, y=105)
band1_label.place(x=627, y=75)
band1_val_label.place(x=639, y=205)

band2.place(x=675, y=105)
band2_label.place(x=663, y=75)
band2_val_label.place(x=679, y=205)

band3.place(x=715, y=105)
band3_label.place(x=708, y=75)
band3_val_label.place(x=719, y=205)

band4.place(x=755, y=105)
band4_label.place(x=748, y=75)
band4_val_label.place(x=759, y=205)

band5.place(x=795, y=105)
band5_label.place(x=788, y=75)
band5_val_label.place(x=799, y=205)

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

window.mainloop()
