import os
import configparser

push_to_talk = False
push_to_talk_key = None
push_to_toggle = False
push_to_toggle_key = None
mute_time_ms = 250

def load_configuration(self):
    config = configparser.ConfigParser()
    try:
        config.read(os.path.expanduser('~/.config/hushboard.cfg'))
    except (configparser.NoSectionError, configparser.MissingSectionHeaderError):
        print("No section header found in file")
        return
    
    default_section = 'Default'

    if not config.has_section(default_section):
        return

    hushConfig = config[default_section]

    if config.has_option(default_section,'PushKey'):
        global push_to_talk
        push_to_talk = True
        global push_to_talk_key
        push_to_talk_key = hushConfig.getint('PushKey')

    if config.has_option(default_section,'ToggleKey'):
        global push_to_toggle
        push_to_toggle = True
        global push_to_toggle_key
        push_to_toggle_key = hushConfig.getint('ToggleKey')
    
    if config.has_option(default_section,'MuteTimeMs'):
        global mute_time_ms
        mute_time_ms = hushConfig.getint('MuteTimeMs')