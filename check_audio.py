import miniaudio
devices = miniaudio.Devices()
captures = devices.get_captures()
for d in enumerate(captures):
    print("{num} = {name}".format(num=d[0], name=d[1]['name']))