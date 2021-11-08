import tkinter
import PIL.Image
import PIL.ImageTk
import cv2
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import style
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import os
from dataProcessing import Data
from tkinter import filedialog as fd
import sys

style.use("ggplot")
matplotlib.use("TkAgg")

PREVIOUS_SLIDER = 1
AVERAGE_VELOCITY = False
VELOCITY = True
ANGLES = False
START_PULL = False
END_PULL = False
FINISH_DRIVE = False
KICK_RECOVERY = False
KICK_PROPULSION = False
FINISH_KICK = False
UPDATE = True
PREVIOUS_ADV_STATE = [not VELOCITY, AVERAGE_VELOCITY, START_PULL, END_PULL, FINISH_DRIVE, KICK_RECOVERY,
                      KICK_PROPULSION, FINISH_KICK, ANGLES]
color = "#ecfbfc"

fig_basic = plt.Figure(figsize=(3.5, 3.5), tight_layout=True)
a = fig_basic.add_subplot(111)
a.grid(False)
fig_adv = plt.Figure(figsize=(3.5, 3.5), tight_layout=True)
ax = fig_adv.add_subplot(111)
ax2 = ax.twinx()
ax2.yaxis.set_label_position("right")
ax2.yaxis.tick_right()
ax.axis([0, 177, 0, 3])
ax2.axis([0, 177, 50, 190])
ax.grid(False)
ax2.grid(False)


def basic_animate(i):
    global PREVIOUS_SLIDER, UPDATE
    if UPDATE:
        UPDATE = False
        pull_data = open("sampleData.txt", "r").read()
        data_list = pull_data.split("\n")
        x_list = []
        y_list = []
        for eachLine in data_list:
            if len(eachLine) > 1:
                y, x = eachLine.split(",")
                x_list.append(float(x))
                y_list.append(float(y))

        a.clear()
        a.grid(False)
        a.axis([0, 177, 0, 3])
        a.set_xlabel("Frames", color="black", fontsize=12)
        a.set_ylabel("M/s Velocity", fontsize=12)
        a.plot(x_list, y_list, color="#f55a5a")


class App:
    def __init__(self, window, window_title, video_source, data_csv):
        global AVERAGE_VELOCITY
        self.window = window
        self.video_source = video_source
        self.window.title(window_title)
        self.window.minsize(1400, 600)
        self.window.maxsize(1400, 600)
        # self.video_source = fd.askopenfilename()
        self.data = Data(data_csv)
        self.velocity_delta = self.data.athlete_vel
        self.side_view_angles = self.data.leg_angles
        self.current_frame = 1
        self.avg_vel_const = self.data.get_average_velocity()

        # open video source (by default this will try to open the computer webcam)
        self.vid = MyVideoCapture(self.video_source)

        # Create a canvas that can fit the above video source size
        self.canvas = tkinter.Canvas(window, width=self.vid.width, height=self.vid.height)
        self.canvas.config(bg=color)
        self.canvas.pack()

        self.slider = tkinter.Scale(window, from_=0, to=self.vid.vid.get(cv2.CAP_PROP_FRAME_COUNT) - 1,
                                    orient='horizontal', length=690, bg=color, bd=4)
        self.slider.place(x=0, y=400)

        self.avg_var = tkinter.BooleanVar()
        self.vel_var = tkinter.BooleanVar()
        self.sp_var = tkinter.BooleanVar()
        self.ep_var = tkinter.BooleanVar()
        self.fd_var = tkinter.BooleanVar()
        self.kr_var = tkinter.BooleanVar()
        self.kp_var = tkinter.BooleanVar()
        self.fk_var = tkinter.BooleanVar()
        self.angle_var = tkinter.BooleanVar()
        self.avg_vel = tkinter.Checkbutton(window, text="Average Velocity", variable=self.avg_var, onvalue=True,
                                           offvalue=False, command=self.sel)
        self.avg_vel.config(bg=color, activebackground=color)
        self.avg_vel.place(x=1100, y=390)

        self.vel = tkinter.Checkbutton(window, text="Current Velocity", variable=self.vel_var, onvalue=True,
                                       offvalue=False, command=self.sel, fg="#f55a5a")
        self.vel.config(bg=color, activebackground=color)
        self.vel.place(x=1100, y=410)
        self.vel.select()

        self.sp = tkinter.Checkbutton(window, text="Start Pull", variable=self.sp_var, onvalue=True,
                                      offvalue=False, command=self.sel, fg="darkgreen")
        self.sp.config(bg=color, activebackground=color)
        self.sp.place(x=1100, y=430)

        self.ep = tkinter.Checkbutton(window, text="End Pull", variable=self.ep_var, onvalue=True,
                                           offvalue=False, command=self.sel, fg="green")
        self.ep.config(bg=color, activebackground=color)
        self.ep.place(x=1100, y=450)

        self.fd = tkinter.Checkbutton(window, text="Finish Drive", variable=self.fd_var, onvalue=True,
                                           offvalue=False, command=self.sel, fg="lightgreen")
        self.fd.config(bg=color, activebackground=color)
        self.fd.place(x=1250, y=390)

        self.kr = tkinter.Checkbutton(window, text="Kick Recovery", variable=self.kr_var, onvalue=True,
                                           offvalue=False, command=self.sel, fg="#179CAD")
        self.kr.config(bg=color, activebackground=color)
        self.kr.place(x=1250, y=410)

        self.kp = tkinter.Checkbutton(window, text="Kick Propulsion", variable=self.kp_var, onvalue=True,
                                           offvalue=False, command=self.sel, fg="#1DC4DA")
        self.kp.config(bg=color, activebackground=color)
        self.kp.place(x=1250, y=430)

        self.fk = tkinter.Checkbutton(window, text="Finish Kick", variable=self.fk_var, onvalue=True,
                                           offvalue=False, command=self.sel, fg="#43d3e6")
        self.fk.config(bg=color, activebackground=color)
        self.fk.place(x=1250, y=450)

        self.angle = tkinter.Checkbutton(window, text="Angle (Leg)", variable=self.angle_var, onvalue=True,
                                      offvalue=False, command=self.sel, fg="lightblue")
        self.angle.config(bg=color, activebackground=color)
        self.angle.place(x=1250, y=470)
        stats = [1, 2, 3]
        # Key Statistics
        table_color = "#bff0f6"
        self.key_stat_label_avgvel = tkinter.Label(window, text="Average Velocity (m/s)",
                                                   borderwidth=1, relief="solid", width=17, bg=table_color)
        self.key_stat_label_avgvel.place(x=705, y=450)
        self.key_stat_label_sr = tkinter.Label(window, text="Stroke Rate (strokes/min)", borderwidth=1, relief="solid",
                                               width=19, bg=table_color)
        self.key_stat_label_sr.place(x=827, y=450)
        self.key_stat_label_sl = tkinter.Label(window, text="Stroke Length (m)", borderwidth=1, relief="solid",
                                               width=14, bg=table_color)
        self.key_stat_label_sl.place(x=963, y=450)

        var_avgvel = tkinter.IntVar()
        var_avgvel.set(self.data.get_average_velocity())
        var_sr = tkinter.IntVar()
        var_sr.set(self.data.get_stroke_rate())
        var_sl = tkinter.IntVar()
        var_sl.set(self.data.get_stroke_length())

        self.key_stat_entry_avgvel = tkinter.Label(window, textvariable=var_avgvel, borderwidth=1, relief="solid",
                                                   width=17)
        self.key_stat_entry_avgvel.config(bg=table_color)
        self.key_stat_entry_avgvel.place(x=705, y=468)
        self.key_stat_entry_sr = tkinter.Label(window, textvariable=var_sr, borderwidth=1, relief="solid", width=19)
        self.key_stat_entry_sr.config(bg=table_color)
        self.key_stat_entry_sr.place(x=827, y=468)
        self.key_stat_entry_sl = tkinter.Label(window, textvariable=var_sl, borderwidth=1, relief="solid", width=14)
        self.key_stat_entry_sl.config(bg=table_color)
        self.key_stat_entry_sl.place(x=963, y=468)

        vel_graph = FigureCanvasTkAgg(fig_basic, master=self.window)
        vel_graph.draw()
        vel_graph.get_tk_widget().place(x=700, y=0)

        adv_graph = FigureCanvasTkAgg(fig_adv, master=self.window)
        adv_graph.draw()
        adv_graph.get_tk_widget().place(x=1050, y=0)

        toolbar = NavigationToolbar2Tk(vel_graph, self.window)
        toolbar.config(bg=color)
        toolbar.update()
        toolbar.place(x=700, y=350)

        toolbar_adv = NavigationToolbar2Tk(adv_graph, self.window)
        toolbar_adv.config(bg=color)
        toolbar_adv.update()
        toolbar_adv.place(x=1050, y=350)

        # After it is called once, the update method will be automatically called every delay milliseconds
        self.delay = 15
        self.update()

        ani = animation.FuncAnimation(fig_basic, basic_animate, interval=150)
        ani_2 = animation.FuncAnimation(fig_adv, self.adv_animate, interval=1000)

        self.window.mainloop()

    def update(self):
        global PREVIOUS_SLIDER, UPDATE
        # Get a frame from the video source
        self.current_frame = self.slider.get()
        if self.current_frame != PREVIOUS_SLIDER:
            UPDATE = True
            self.vid.vid.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)
            ret, frame = self.vid.get_frame()
            frame = cv2.resize(frame, (700, 400))

            PREVIOUS_SLIDER = self.current_frame
            if "sampleData.txt" in os.listdir(r"./"):
                os.remove(r"./sampleData.txt")

            new_data = open(r"./sampleData.txt", "w")
            for x, y in zip(self.velocity_delta[:self.current_frame], list(range(self.current_frame))):
                new_data.write(f"{x},{y}\n")


            if ret:
                self.photo = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(frame))
                self.canvas.create_image(0, 0, image=self.photo, anchor=tkinter.NW)

        self.window.after(self.delay, self.update)

    def adv_animate(self, i):
        global PREVIOUS_ADV_STATE
        current_state = [VELOCITY, AVERAGE_VELOCITY, START_PULL, END_PULL, FINISH_DRIVE, KICK_RECOVERY,
                         KICK_PROPULSION, FINISH_KICK, ANGLES]
        if current_state != PREVIOUS_ADV_STATE:
            ax.cla()
            ax2.cla()
            ax.grid(False)
            ax2.grid(False)
            ax2.yaxis.set_label_position("right")
            ax2.yaxis.tick_right()
            ax.axis([0, 177, 0, 3])
            ax2.axis([0, 177, 50, 190])
            ax.set_xlabel("Frames", color="black", fontsize=12)
            ax.set_ylabel("M/s Velocity", fontsize=12)
            ax2.set_ylabel("Angle (Degrees)")

            PREVIOUS_ADV_STATE = current_state
            avg_vel_const = [self.avg_vel_const for _ in range(len(self.velocity_delta))]
            if VELOCITY:
                ax.plot(list(range(len(self.velocity_delta))), self.data.athlete_vel, zorder=-1, color="#f55a5a")
            if AVERAGE_VELOCITY:
                ax.plot(list(range(len(self.velocity_delta))), avg_vel_const, zorder=-1, color="black", linestyle="dashed")
            if START_PULL:
                ax.scatter(self.data.start_pull, [1.3 for _ in range(len(self.data.start_pull))], color="darkgreen", zorder=1,
                           marker='x', s=20,  label="hello")
            if END_PULL:
                ax.scatter(self.data.end_pull, [1.3 for _ in range(len(self.data.end_pull))], color="green", zorder=1,
                           marker='x', s=20)
            if FINISH_DRIVE:
                ax.scatter(self.data.finish_drive, [1 for _ in range(len(self.data.finish_drive))], color="lightgreen",
                           zorder=1, marker='x', s=20)
            if KICK_RECOVERY:
                ax.scatter(self.data.kick_recovery, [0.8 for _ in range(len(self.data.kick_recovery))], color="#179CAD",
                           zorder=1, marker='x', s=20)
            if KICK_PROPULSION:
                ax.scatter(self.data.kick_propulsion, [0.8 for _ in range(len(self.data.kick_propulsion))], color="#1DC4DA",
                           zorder=1, marker='x', s=20)
            if FINISH_KICK:
                ax.scatter(self.data.finish_kick, [0.6 for _ in range(len(self.data.finish_kick))], color="#43d3e6", zorder=1,
                           marker='x', s=20)
            if ANGLES:
                ax2.plot(list(range(len(self.side_view_angles))), self.data.leg_angles, zorder=-1, color="lightblue")


    def sel(self):
        global AVERAGE_VELOCITY, VELOCITY, START_PULL, END_PULL, \
            FINISH_DRIVE, KICK_RECOVERY, KICK_PROPULSION, FINISH_KICK, ANGLES
        AVERAGE_VELOCITY = self.avg_var.get()
        VELOCITY = self.vel_var.get()
        START_PULL = self.sp_var.get()
        END_PULL = self.ep_var.get()
        FINISH_DRIVE = self.fd_var.get()
        KICK_RECOVERY = self.kr_var.get()
        KICK_PROPULSION = self.kp_var.get()
        FINISH_KICK = self.fk_var.get()
        ANGLES = self.angle_var.get()


class MyVideoCapture:
    def __init__(self, video_source=0):
        # Open the video source
        self.vid = cv2.VideoCapture(video_source)
        if not self.vid.isOpened():
            raise ValueError("Unable to open video source", video_source)

        # Get video source width and height
        self.width = 1400
        self.height = 600

    def get_frame(self):
        if self.vid.isOpened():
            ret, frame = self.vid.read()
            if ret:
                # Return a boolean success flag and the current frame converted to BGR
                return ret, cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            else:
                return ret, None

    # Release the video source when the object is destroyed
    def __del__(self):
        if self.vid.isOpened():
            self.vid.release()

print('Number of arguments:', len(sys.argv), 'arguments.')
print('Argument List:', str(sys.argv))
# Create a window and pass it to the Application object
App(tkinter.Tk(), "Tkinter and OpenCV",
    video_source=sys.argv[1], data_csv=sys.argv[2])
