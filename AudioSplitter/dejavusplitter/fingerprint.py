import subprocess
import os

import numpy as np
import matplotlib.mlab as mlab
import matplotlib.pyplot as plt

from pydub import AudioSegment
from scipy.spatial.distance import euclidean
from fastdtw import fastdtw

######################################################################
# Sampling rate, related to the Nyquist conditions, which affects
# the range frequencies we can detect.
DEFAULT_FS = 44100

######################################################################
# Size of the FFT window, affects frequency granularity
DEFAULT_WINDOW_SIZE = 4096

######################################################################
# Ratio by which each sequential window overlaps the last and the
# next window. Higher overlap will allow a higher granularity of offset
# matching, but potentially more fingerprints.
DEFAULT_OVERLAP_RATIO = 0.5

######################################################################
# Minimum amplitude in spectrogram in order to be considered a peak.
# This can be raised to reduce number of fingerprints, but can negatively
# affect accuracy.
DEFAULT_AMP_MIN = 15

######################################################################
# Number of cells around an amplitude peak in the spectrogram in order
# for Dejavu to consider it a spectral peak. Higher values mean less
# fingerprints and faster matching, but can potentially affect accuracy.
PEAK_NEIGHBORHOOD_SIZE = 250

######################################################################
# the range of audio clip which is divided for processing
# if the source audio file is too long, FFT doesn't work
# because of memory limitation
SPLIT_INTERVAL = 3


def fingerprint(file):
    cvt_file = convert_to_wav(file)
    sound = AudioSegment.from_wav(cvt_file)
    return _fingerprint(np.fromstring(sound.raw_data, np.int16))


def recognize(file, dest):
    maxima_pairs = []
    for i in range(len(dest)):
        for j in range(len(dest[i])):
            maxima_pairs.append([i, dest[i][j]])

    cvt_file = convert_to_wav(file)
    sound = AudioSegment.from_wav(cvt_file)

    split_points = []
    interval = SPLIT_INTERVAL * 60 * 1000
    if len(sound) > interval:
        for i in range(0, len(sound), interval):
            if i + interval > len(sound):
                maxima_list = _fingerprint(np.fromstring(sound[i:len(sound)].raw_data, np.int16))
                split_points.extend(_match(maxima_list, maxima_pairs, len(dest), i, len(sound) - i / len(maxima_list)))
            else:
                maxima_list = _fingerprint(np.fromstring(sound[i:i + interval].raw_data, np.int16))
                split_points.extend(_match(maxima_list, maxima_pairs, len(dest), i, interval / len(maxima_list)))
    else:
        maxima_list = _fingerprint(np.fromstring(sound.raw_data, np.int16))
        split_points.extend(_match(maxima_list, maxima_pairs, len(dest), 0, len(sound) / len(maxima_list)))

    return split_points, len(sound)


def _match(src, dest, cmp_width, start_ms, unit_ms, plot=False):
    print('start time(s):', start_ms / 1000, '(s)')
    distance_list = []
    for i in range(0, len(src)):
        temp = []
        for j in range(cmp_width):
            if i + j > len(src) - 1:
                break
            for k in range(len(src[i + j])):
                temp.append([j, src[i + j][k]])
        if len(temp) == 0:
            continue
        distance, path = fastdtw(dest, temp, dist=euclidean)
        distance_list.append(distance)

    dist_pairs = []
    d_pairs = []
    t_pairs = []
    is_consecutive = False
    for i in range(len(distance_list)):
        if distance_list[i] < 2500:
            is_consecutive = True
            d_pairs.append(distance_list[i])
            t_pairs.append(start_ms + i * unit_ms)
        else:
            if is_consecutive:
                is_consecutive = False
                dist_pairs.append([d_pairs, t_pairs])
                d_pairs = []
                t_pairs = []

    ret = []
    for each in dist_pairs:
        min_dist = min(each[0])
        min_index = each[0].index(min_dist)
        ret.append([each[0][min_index], each[1][min_index]])

    if plot:
        for each in dist_pairs:
            print(each)
        plt.plot(distance_list)
        plt.show()

    return ret


def _fingerprint(data, plot=False):
    # FFT the signal and extract frequency components
    params = {
        "NFFT": DEFAULT_WINDOW_SIZE,
        "Fs": DEFAULT_FS,
        "window": mlab.window_hanning,
        "noverlap": int(DEFAULT_WINDOW_SIZE * DEFAULT_OVERLAP_RATIO)
    }
    specgram, freq, time = mlab.specgram(data, **params)

    # apply log transform since specgram() returns linear array
    specgram = 10 * np.log10(specgram)
    specgram[specgram == -np.inf] = 0  # replace infs with zeros

    if plot:
        plt.plot(data)
        plt.xlabel('time (s)')
        plt.ylabel('amplitude (dB)')
        plt.show()

        spec, freq, time, im = plt.specgram(data, **params)
        plt.colorbar()
        plt.xlabel('time (s)')
        plt.ylabel('frequency (hz)')
        plt.show()

    # find local maxima
    local_maxima = get_2D_peaks(specgram)

    return local_maxima


def get_2D_peaks(arr2D, plot=False):
    frequency_idx = []
    time_idx = []

    ret = []
    arr2D = np.transpose(arr2D)
    for t_index in range(len(arr2D)):
        temp_freq = []
        for f_index in range(0, len(arr2D[t_index]), PEAK_NEIGHBORHOOD_SIZE):
            max = arr2D[t_index][f_index:f_index + PEAK_NEIGHBORHOOD_SIZE].max()

            if max > DEFAULT_AMP_MIN:
                temp_freq.append(int(np.where(arr2D[t_index] == max)[0]))
                time_idx.append(t_index)
                frequency_idx.append(int(np.where(arr2D[t_index] == max)[0]))

        ret.append(temp_freq)

    if plot:
        arr2D = np.transpose(arr2D)

        # scatter of the peaks
        plt.imshow(arr2D, aspect='auto')
        plt.colorbar()
        plt.scatter(time_idx, frequency_idx, s=30, c='r', marker='x')
        plt.xlabel('Time')
        plt.ylabel('Frequency')
        plt.title("Spectrogram")
        plt.gca().invert_yaxis()
        plt.show()

    return ret


def convert_to_wav(file):
    converted_file = 'temp.wav'

    if os.path.exists(converted_file):
        os.remove(converted_file)

    # audio code: PCM, channel: 1, frame rate: 44.1k
    cmd = 'ffmpeg -i {} -acodec pcm_s16le -ac 1 -ar {} {}'.format(file, DEFAULT_FS, converted_file)

    try:
        proc = subprocess.Popen(cmd)
        proc.communicate()
        print('convert is done...')
    except:
        print('raised exception while converting...')

    return converted_file
