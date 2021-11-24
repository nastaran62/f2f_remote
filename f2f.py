
import os
import random
import logging
import datetime

from octopus_sensing.windows.timer_window import TimerWindow
from windows import ImageWindow, MessageButtonWindow

#from octopus_sensing.devices.audio_streaming import AudioStreaming
from octopus_sensing.devices.camera_streaming import CameraStreaming
#from octopus_sensing.devices.shimmer3_streaming import Shimmer3Streaming#
#from octopus_sensing.devices.openbci_streaming import OpenBCIStreaming
from octopus_sensing.device_coordinator import DeviceCoordinator
from octopus_sensing.monitoring_endpoint import MonitoringEndpoint

from octopus_sensing.common.message_creators import start_message, stop_message
import time
import argparse
from screeninfo import get_monitors
import gi
from gi.repository import Gtk, GdkPixbuf, GLib, Gdk
gi.require_version('Gtk', '3.0')
gi.require_version('Gst', '1.0')

import os
import random
import csv

EMOTIONS = {"1": "High-Valence, High-Arousal",
            "2": "High-Valence, Low-Arousal",
            "3": "Low-Valence, High-Arousal",
            "4": "Low-Valence, Low-Arousal"}

def read_stimuli_order(subject_id):
    stimuli_order_file_path = "stimuli/f2f/p{}_stimuli.csv".format(subject_id)
    order = []
    with open(stimuli_order_file_path, "r") as csv_file:
        reader = csv.reader(csv_file)
        for row in reader:
            order.append(row[0])
    return order

STIMULI_PATH = "stimuli/all_images/"

class BackgroudWindow(Gtk.Window):
    def __init__(self, experiment_id, subject_id, device_coordinator):
        os.makedirs("logs", exist_ok=True)
        time_str = datetime.datetime.strftime(datetime.datetime.now(),
                                              "%Y-%m-%dT%H-%M-%S")
        logging.basicConfig(filename='logs/exp2_f2f_log_{0}_{1}.log'.format(experiment_id, time_str),
                            level=logging.DEBUG)
        self._device_coordinator = device_coordinator
        self._experiment_id = experiment_id

        self._stimuli_list = read_stimuli_order(subject_id)

        self._index = 0
        logging.info("Emotion order is {}".format(self._stimuli_list))

        Gtk.Window.__init__(self, title="")
        image_box = Gtk.Box()
        monitors = get_monitors()
        monitors1 = []
        window = Gtk.Window()
        self.screen = window.get_screen()
        print(self.screen)
        for m in range(self.screen.get_n_monitors()):
            monitor = self.screen.get_monitor_geometry(m)
            monitors1.append([monitor.x, monitor.y, monitor.width, monitor.height])
            print(monitor.x, monitor.y, monitor.width, monitor.height)
        
        image_width = monitors[0].width
        image_height = monitors[0].height
        print(image_width, image_height)
        background_path = "images/gray_image.jpg"
        pixbuf = \
            GdkPixbuf.Pixbuf.new_from_file_at_scale(background_path,
                                                    image_width,
                                                    image_height, False)
        image = Gtk.Image()
        image.set_from_pixbuf(pixbuf)
        image_box.pack_start(image, False, False, 0)
        self.add(image_box)

        self.image_window = ImageWindow("image_window", monitor_no=1)
        self.image_window.set_image(background_path)


    def show(self, *args):
        '''
        Shows the background window (A gray image)
        '''
        self.connect("destroy", Gtk.main_quit)
        self.fullscreen()
        self.show_all()
        self.image_window.show_window()

        GLib.timeout_add_seconds(3, self._show_message)
        GLib.timeout_add_seconds(1, self._move_image_window)
        Gtk.main()

    def _move_image_window(self, *args):
        os.system("wmctrl -ir $(wmctrl -l |grep image_window |grep -v grep |cut -d ' ' -f1) -e 0,1200,0,-1,-1")

    def _show_message(self, *args, message="Start"):
        '''
        Showing a message before each stimuli
        '''
        logging.info("Start time {0}".format(datetime.datetime.now()))
        start = \
            MessageButtonWindow("Info", message)
        start.show()
        start.connect("destroy", self._show_fixation_cross)

    def _show_fixation_cross(self, *args):
        '''
        Showing fixation cross before each stimuli
        '''
        logging.info("Fixation cross {0}".format(datetime.datetime.now()))
        self.image_window.set_image("images/fixation_cross.jpg")
        #self._device_coordinator.dispatch(start_message(self._experiment_id,
        #                                                self._stimuli_list[self._index][:-4]))
        #self.image_window.show_window()

        GLib.timeout_add_seconds(3, self._show_stimuli)

    def _show_stimuli(self, *args):
        '''
        Showing stimuli
        '''
        logging.info("Stimuli {0} - {1}".format(self._stimuli_list[self._index],
                                                datetime.datetime.now()))
        image_path = STIMULI_PATH + self._stimuli_list[self._index]
        self.image_window.set_image(image_path)
        #self.image_window.show_window()
        GLib.timeout_add_seconds(6, self._show_timer)

    def _show_timer(self, *args):
        '''
        Showing timer
        '''
        logging.info("Start of Conversation {0} - {1}".format(self._stimuli_list[self._index],
                                                              datetime.datetime.now()))
        message = \
            start_message(self._experiment_id,
                          self._stimuli_list[self._index])

        timer = TimerWindow(EMOTIONS[self._stimuli_list[self._index][0]])
        #self._device_coordinator.dispatch(message)
        timer.show_window()
        timer.connect("destroy", self._questionnaire)

    def _questionnaire(self, *args):
        message = \
            stop_message(self._experiment_id,
                         self._stimuli_list[self._index])
        # self._device_coordinator.dispatch(message)
        self._index += 1
        if self._index >= 2:
            #self._device_coordinator.terminate()
            self._done()
        else:
            self._show_message(message="Please answer the questionnaire.")

    def _done(self, *args):

        message = stop_message(self._experiment_id, 0)
        self.image_window.set_image("images/done_image.jpg")
        self.image_window.show_and_destroy_window(3)
        self.image_window.connect("destroy", self._terminate)

    def _terminate(self, *args):
        logging.info("End time{0}".format(datetime.datetime.now()))
        self.destroy()


def get_input_parameters():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--subject_id", help="The subject ID", default=0)
    #parser.add_argument("-t", "--task_id", help="The task ID", default=1)
    args = parser.parse_args()
    subject_id = args.subject_id
    task_id = 1  # args.task_id
    return subject_id, task_id


def main():
    main_camera = "/dev/v4l/by-id/usb-Intel_R__RealSense_TM__Depth_Camera_415_Intel_R__RealSense_TM__Depth_Camera_415-video-index0"

    subject_id, task_id = get_input_parameters()
    experiment_id = str(subject_id).zfill(2) + "-" + str(task_id).zfill(2)
    output_path = "output/p{0}".format(subject_id)
    os.makedirs(output_path, exist_ok=False)


    #openbci = OpenBCIStreaming(name="OpenBCI", output_path=output_path)
    #shimmer = Shimmer3Streaming(name="Shimmer", output_path=output_path)
#    audio = AudioStreaming(name="Audio", output_path=output_path)

    camera = \
        CameraStreaming(name="Camera",
                        output_path=output_path,
                        camera_no=0,
                        #camera_path=main_camera,
                        image_width=640,
                        image_height=480)
    device_coordinator = DeviceCoordinator()
    #device_coordinator.add_devices([camera])

    # Make delay for initializing all processes
    time.sleep(5)
    # MonitoringEndpoint(device_coordinator).start()
    main_window = BackgroudWindow(experiment_id, subject_id, device_coordinator)
    main_window.show()


main()
