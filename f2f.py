'''
Steps:
0- Turn on devices and test camera view
1- Run `sudo rfcomm connect rfcomm0 00:06:66:F0:95:95` in another terminal
2- Start the experiment with passing the subject ID
3- Run monitoring (Get the IP address before) before pressing the start button
'''

import os
import logging
import datetime
import sys
import time
import argparse
import csv
from scipy import signal

from screeninfo import get_monitors
sys.path.insert(0, '../octopus-sensing/')

from octopus_sensing.windows.timer_window import TimerWindow
from octopus_sensing.devices import AudioStreaming
from octopus_sensing.devices import CameraStreaming
from octopus_sensing.devices import BrainFlowOpenBCIStreaming
from octopus_sensing.devices.shimmer3_streaming import Shimmer3Streaming
from octopus_sensing.device_coordinator import DeviceCoordinator
from octopus_sensing.monitoring_endpoint import MonitoringEndpoint
from octopus_sensing.preprocessing.preprocess_devices import preprocess_devices
from octopus_sensing.common.message_creators import start_message, stop_message

from windows import ImageWindow, MessageButtonWindow
from prepare_stimuli import prepare_stimuli_list

import gi
from gi.repository import Gtk, GdkPixbuf, GLib, Gdk
gi.require_version('Gtk', '3.0')
gi.require_version('Gst', '1.0')


EMOTIONS = {"1": "High-Valence, High-Arousal",
            "2": "High-Valence, Low-Arousal",
            "3": "Low-Valence, High-Arousal",
            "4": "Low-Valence, Low-Arousal"}

def read_stimuli_order(subject_id):
    stimuli_order_file_path = "stimuli/f2f/p{}_stimuli.csv".format(str(subject_id).zfill(2))
    print(stimuli_order_file_path)
    if not os.path.exists(stimuli_order_file_path):
        prepare_stimuli_list(subject_id)
    order = []
    with open(stimuli_order_file_path, "r") as csv_file:
        reader = csv.reader(csv_file)
        for row in reader:
            order.append(row[0])
    print(order)
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
        self.navigator_image_window = ImageWindow("image_window", monitor_no=0)
        self.navigator_image_window.set_image(background_path)


    def show(self, *args):
        '''
        Shows the background window (A gray image)
        '''
        self.connect("destroy", Gtk.main_quit)
        self.fullscreen()
        self.show_all()
        self.image_window.show_window()
        self.navigator_image_window.show_window()

        GLib.timeout_add_seconds(5, self._show_message)
        GLib.timeout_add_seconds(1, self._move_image_window)
        Gtk.main()

    def _move_image_window(self, *args):
        os.system("wmctrl -ir $(wmctrl -l |grep image_window |grep -v grep |cut -d ' ' -f1) -e 0,1200,0,-1,-1")

    def _show_message(self, *args, message="Start"):
        '''
        Showing a message before each stimuli
        '''

        logging.info("Start time {0}".format(datetime.datetime.now()))
        message = \
            MessageButtonWindow("Info", message)
        message.show()

        if self._index >= 8:
            message.connect("destroy", self._done)
        else:
            message.connect("destroy", self._show_fixation_cross)

    def _show_fixation_cross(self, *args):
        '''
        Showing fixation cross before each stimuli
        '''
        logging.info("Fixation cross {0}".format(datetime.datetime.now()))
        self.image_window.set_image("images/fixation_cross.jpg")
        self.navigator_image_window.set_image("images/fixation_cross.jpg")
        message = \
            start_message(self._experiment_id,
                          self._stimuli_list[self._index][:-4])
        self._device_coordinator.dispatch(message)

        GLib.timeout_add_seconds(3, self._show_stimuli)

    def _show_stimuli(self, *args):
        '''
        Showing stimuli
        '''
        logging.info("Stimuli {0} - {1}".format(self._stimuli_list[self._index],
                                                datetime.datetime.now()))
        image_path = STIMULI_PATH + self._stimuli_list[self._index]
        self.image_window.set_image(image_path)
        self.navigator_image_window.set_image(image_path)
        GLib.timeout_add_seconds(6, self._show_timer)

    def _show_timer(self, *args):
        '''
        Showing timer
        '''
        logging.info("Start of Conversation {0} - {1}".format(self._stimuli_list[self._index],
                                                              datetime.datetime.now()))

        image_path = STIMULI_PATH + self._stimuli_list[self._index]
        timer = TimerWindow("Timer", message=EMOTIONS[self._stimuli_list[self._index][0]],
                            width=600,
                            font_size=20)
        timer.show_window()
        timer.connect("destroy", self._questionnaire)

    def _questionnaire(self, *args):
        message = \
            stop_message(self._experiment_id,
                         self._stimuli_list[self._index][:-4])
        self._device_coordinator.dispatch(message)
        self._index += 1
        self._show_message(message="Please answer the questionnaire.")

    def _done(self, *args):

        self._device_coordinator.terminate()
        self.image_window.set_image("images/done_image.jpg")
        self.image_window.show_and_destroy_window(3)
        self.image_window.connect("destroy", self._terminate)
        self.navigator_image_window.set_image("images/done_image.jpg")
        self.navigator_image_window.show_and_destroy_window(3)
        self.navigator_image_window.connect("destroy", self._terminate)

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

    #main_camera = "/dev/v4l/by-id/usb-046d_081b_97E6A7D0-video-index0"
    subject_id, task_id = get_input_parameters()
    experiment_id = str(subject_id).zfill(2) + "-" + str(task_id).zfill(2)
    output_path = "output/p{0}".format(str(subject_id).zfill(2))
    if not os.path.exists(output_path):
        os.makedirs(output_path, exist_ok=False)
    else:
        output_path = output_path + str(time.time())[8:10]
        os.makedirs(output_path, exist_ok=False)

    
    openbci = \
        BrainFlowOpenBCIStreaming(name="eeg",
                                  output_path=output_path,
                                  board_type="cyton-daisy",
                                  channels_order=["Fp1", "Fp2", "F7", "F3", 
                                                   "F4", "F8", "T3", "C3",
                                                   "C4", "T4", "T5", "P3", 
                                                   "P4", "T6", "O1", "O2"],
                                  serial_port="/dev/ttyUSB0")
    
    
    shimmer = Shimmer3Streaming(name="shimmer", output_path=output_path)
    audio = AudioStreaming(2, name="Audio", output_path=output_path)

    camera = \
        CameraStreaming(name="webcam",
                        output_path=output_path,
                        camera_path=main_camera,
                        image_width=640,
                        image_height=480)
    device_coordinator = DeviceCoordinator()
    device_coordinator.add_devices([audio, camera, openbci, shimmer])

    # Make delay for initializing all processes
    time.sleep(5)
    monitoring_endpoint = MonitoringEndpoint(device_coordinator)
    monitoring_endpoint.start()
    main_window = BackgroudWindow(experiment_id, subject_id, device_coordinator)
    main_window.show()
    monitoring_endpoint.stop()

    preprocess_devices(device_coordinator,
                       "preprocessed_output",
                       openbci_sampling_rate=125,
                       signal_preprocess=True,
                       shimmer3_sampling_rate=128)


main()
