'''
Steps:
0- Turn on devices and test camera view
1- Run `sudo rfcomm connect rfcomm0 00:06:66:F0:95:95` in another terminal
2- Start the experiment with passing the subject ID
3- Run monitoring (Get the IP address before) before pressing the start button
'''

import os
import time
import sys
import argparse
sys.path.insert(0, '../octopus-sensing/')
from octopus_sensing.device_coordinator import DeviceCoordinator
from octopus_sensing.devices import AudioStreaming
from octopus_sensing.devices import CameraStreaming
from octopus_sensing.devices import BrainFlowOpenBCIStreaming
from octopus_sensing.devices.shimmer3_streaming import Shimmer3Streaming

from octopus_sensing.monitoring_endpoint import MonitoringEndpoint
from octopus_sensing.preprocessing.preprocess_devices import preprocess_devices
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
    main_camera = "/dev/v4l/by-id/usb-Intel_R__RealSense_TM__Depth_Camera_415_Intel_R__RealSense_TM__Depth_Camera_415-video-index0"
    subject_id, task_id = get_input_parameters()
    experiment_id = str(subject_id).zfill(2) + "-" + str(task_id).zfill(2)
    output_path = "output_remote/p{0}".format(str.zfill(subject_id,2))
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
    
    
    audio = AudioStreaming(2, name="audio", output_path=output_path)

    camera = \
        CameraStreaming(name="webcam",
                        output_path=output_path,
                        #camera_no=os.path.realpath(main_camera),
                        camera_path=main_camera,
                        image_width=640,
                        image_height=480)
    device_coordinator = DeviceCoordinator()
    device_coordinator.add_devices([camera, audio, openbci, shimmer])

    monitoring_endpoint = MonitoringEndpoint(device_coordinator)
    monitoring_endpoint.start()

    # Add your devices
    message_endpoint = DeviceMessageHTTPEndpoint(device_coordinator, port=9331)
    print("start listening")
    message_endpoint.start()

    
    while True:
        key = input("Please enter q to stop")
        if key == "q":
            break
    
    message_endpoint.stop()
    monitoring_endpoint.stop()
    try:
        device_coordinator.terminate()
    except:
        pass

    preprocess_devices(device_coordinator,
                       "preprocessed_remote_output",
                       openbci_sampling_rate=125,
                       signal_preprocess=True,
                       shimmer3_sampling_rate=128)

main()
