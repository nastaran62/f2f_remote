'''
Steps:
0- Turn on devices and test camera view
1- Run `sudo rfcomm connect rfcomm0 00:06:66:F0:95:95` in another terminal
2- Start the experiment with passing the subject ID
3- Run monitoring (Get the IP address before) before pressing the start button
'''

import os
import sys
import argparse
sys.path.insert(0, '../octopus-sensing/')
from octopus_sensing.device_coordinator import DeviceCoordinator
from octopus_sensing.devices import AudioStreaming
from octopus_sensing.devices import CameraStreaming
from octopus_sensing.devices import BrainFlowOpenBCIStreaming
#from octopus_sensing.devices.shimmer3_streaming import Shimmer3Streaming#

from octopus_sensing.device_message_endpoint import DeviceMessageHTTPEndpoint

def get_input_parameters():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--subject_id", help="The subject ID", default=0)
    #parser.add_argument("-t", "--task_id", help="The task ID", default=1)
    args = parser.parse_args()
    subject_id = args.subject_id
    task_id = 1  # args.task_id
    return subject_id, task_id

def main():
    device_coordinator = DeviceCoordinator()
    main_camera = "/dev/v4l/by-id/usb-046d_081b_97E6A7D0-video-index0"
    subject_id, task_id = get_input_parameters()
    experiment_id = str(subject_id).zfill(2) + "-" + str(task_id).zfill(2)
    output_path = "output_remote/p{0}".format(subject_id)
    os.makedirs(output_path, exist_ok=False)

    
    openbci = \
        BrainFlowOpenBCIStreaming(name="eeg",
                                    output_path=output_path,
                                    board_type="cyton-daisy",
                                    channels_order=["Fp1", "Fp2", "F7", "F3", 
                                                    "F4", "F8", "T3", "C3",
                                                    "C4", "T4", "T5", "P3", 
                                                    "P4", "T6", "O1", "O2"])
    
    #shimmer = Shimmer3Streaming(name="Shimmer", output_path=output_path)
    audio = AudioStreaming(0, name="Audio", output_path=output_path)

    camera = \
        CameraStreaming(name="webcam",
                        output_path=output_path,
                        #camera_no=os.path.realpath(main_camera),
                        camera_path=main_camera,
                        image_width=640,
                        image_height=480)
    device_coordinator = DeviceCoordinator()
    device_coordinator.add_devices([camera, audio, openbci])

    # Add your devices
    message_endpoint = DeviceMessageHTTPEndpoint(device_coordinator)
    print("start listening")
    message_endpoint.start()

    
    while True:
        key = input("Please enter qt to stop")
        if key == "qt":
            break
    
    message_endpoint.stop()

main()