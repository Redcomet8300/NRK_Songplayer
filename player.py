import os
import argparse
from mido import MidiFile
import keyboard
import time
import json

# Define octave interval
octave_interval = 12

# Define pitch values for the mandolin in Naraka: Bladepoint
c3_pitch = 48
c5_pitch = 72
b5_pitch = 83

# Define note table for the mandolin
keytable = "z?x?cv?b?n?m" + "a?s?df?g?h?j" + "q?w?er?t?y?u"
notetable = "C?D?EF?G?A?B"

# Define playing state
play_state = 'idle'

# Convert pitch to note name
def note_name(pitch):
    pitch_index = pitch % octave_interval
    if pitch_index < 0:
        return '-'
    pre = notetable[pitch_index]
    if pre == '?':
        pre = notetable[pitch_index - 1] + '#'
    return pre + str(pitch // octave_interval - 1)

# Check if a note is playable
def midi_playable(event):
    if event.is_meta or event.type != 'note_on':
        return False
    return True

# Find the best shifting pitch
def find_best_shift(midi_data):
    note_counter = [0] * octave_interval
    octave_list = [0] * 11

    for event in midi_data:
        if not midi_playable(event):
            continue

        for i in range(octave_interval):
            note_pitch = (event.note + i) % octave_interval
            if keytable[note_pitch] != '?':
                note_counter[i] += 1
                note_octave = (event.note + i) // octave_interval
                octave_list[note_octave] += 1

    max_note = max(range(len(note_counter)), key=note_counter.__getitem__)
    shifting = 0
    counter = 0

    for i in range(len(octave_list) - 3):
        amount = sum(octave_list[i: i + 3])

        if amount > counter:
            counter = amount
            shifting = i

    return int(max_note + (4 - shifting) * octave_interval)

# Play function
def play(midi, shifting):
    global play_state
    play_state = 'playing'
    print('Start playing')

    for event in midi:
        if play_state != 'playing':
            break

        time.sleep(event.time)

        if not midi_playable(event):
            continue

        pitch = event.note + shifting
        original_pitch = pitch

        if pitch < c3_pitch:
            pitch = pitch % octave_interval + c3_pitch
        elif pitch > b5_pitch:
            pitch = pitch % octave_interval + c5_pitch

        if pitch < c3_pitch or pitch > b5_pitch:
            print('skip this note')
            continue

        key_press = keytable[pitch - c3_pitch]

        print(
            f"original key: {note_name(original_pitch)}({original_pitch}) Play key: {note_name(pitch)}({pitch}) Press: {key_press.upper()}\n")

        keyboard.send(key_press)

# Keyboard control function
def control(*args):
    global play_state
    if play_state == 'playing':
        play_state = 'pause'
    elif play_state == 'idle':
        keyboard.call_later(play, args=args, delay=1)

# Main function
if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='MIDI file auto player for Naraka: Bladepoint mandolin')
    parser.add_argument('config', nargs="?", type=str, help='path to config JSON file')
    args = parser.parse_args()
    config_path = args.config

    if not config_path:
        config_path = os.path.join(os.path.dirname(
            os.path.realpath(__file__)), 'config.json')

    # Read the configuration from the JSON file
    with open(config_path, 'r') as config_file:
        config = json.load(config_file)

    folder_path = config.get('folder_path')
    song_file = config.get('song_file')

    if not folder_path or not song_file:
        print("Error: Please provide valid folder_path and song_file in the config JSON.")
    else:
        # Construct the full path to the MIDI file
        midi_path = os.path.join(folder_path, song_file)

        midi = MidiFile(midi_path)
        shifting = find_best_shift(midi)
        print("Press '\\' to play/pause, and press 'backspace' to exit.\n")

        keyboard.add_hotkey('\\', lambda: control(midi, shifting),
                            suppress=True, trigger_on_release=True)

        keyboard.wait('backspace', suppress=True)
