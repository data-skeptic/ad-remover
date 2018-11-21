import subprocess
import os
import threading
import time

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

######################################################################
# the limit of distance to get matched poitns
# after fast DTW algorithm implements
DISTANCE_LIMIT = 3000

######################################################################
# minimum distance points list
split_points = []


class MyThread(threading.Thread):
    def __init__(self, thread_id, list1, list2, length, index, unit):
        threading.Thread.__init__(self)
        self.thread_id = thread_id
        self.list1 = list1
        self.list2 = list2
        self.length = length
        self.index = index
        self.unit = unit

    def run(self):
        _match(self.thread_id, self.list1, self.list2, self.length, self.index, self.unit)


def fingerprint(file):
    """
    This converts input audio into 44.1K-mono wav file.
    :param file: the full path of the input audio
    :return: maxima series
    """

    cvt_file = convert_to_wav(file)

    if not cvt_file:
        return False

    sound = AudioSegment.from_wav(cvt_file)
    return _fingerprint(np.fromstring(sound.raw_data, np.int16))


def recognize(file, dest):
    """
    This fingerprints each part of the source audio and match them with split clip.
    :param file: source audio file
    :param dest: split audio file
    :return:
    """

    # convert maxima series into the list of [index of time series, frequency value]
    # e.g. [[f1, f2], [f3]] -> [[0, f1], [0, f2], [1, f3]]
    maxima_pairs = []
    for i in range(len(dest)):
        for j in range(len(dest[i])):
            maxima_pairs.append([i, dest[i][j]])

    # convert source audio into the mono wav file
    cvt_file = convert_to_wav(file)

    if not cvt_file:
        return False, False

    sound = AudioSegment.from_wav(cvt_file)

    threads = []
    interval = SPLIT_INTERVAL * 60 * 1000  # interval value for dividing the source audio
    if len(sound) > interval:
        for i in range(0, len(sound), interval):
            if i + interval > len(sound):  # last segment of source audio
                maxima_list = _fingerprint(np.fromstring(sound[i:len(sound)].raw_data, np.int16))

                thread = MyThread(i + 1, maxima_list, maxima_pairs, len(dest), i, len(sound) - i / len(maxima_list))
                threads.append(thread)
            else:  # full segments of which length is same as interval
                maxima_list = _fingerprint(np.fromstring(sound[i:i + interval].raw_data, np.int16))

                thread = MyThread(i + 1, maxima_list, maxima_pairs, len(dest), i, interval / len(maxima_list))
                threads.append(thread)

        for each in threads:
            each.start()

        for each in threads:
            each.join()
    else:
        maxima_list = _fingerprint(np.fromstring(sound.raw_data, np.int16))
        _match(1, maxima_list, maxima_pairs, len(dest), 0, len(sound) / len(maxima_list))

    return split_points, len(sound)


def _match(thread_id, src, dest, cmp_width, start_ms, unit_ms, plot=False):
    """
    This compares src with dest and gets matched point from source audio file.
    :param src: source audio file
    :param dest: split audio file
    :param cmp_width: the width of compare window
                     (generally the length of time series of split file)
    :param start_ms: start time of each segment
    :param unit_ms: the length of time of unit value of time axis
    :param plot: show the plot
    :return: matched value list ([[distance, time], ...])
    """

    print('>>> Thread {} : {} point'.format(thread_id, start_ms / 1000))

    dist_pairs = []  # 2-d list of matched points
    d_pairs = []  # distance list of consecutive values
    t_pairs = []  # time list of consecutive values
    is_consecutive = False
    distance_list = []
    half_of_cpm_width = cmp_width // 4
    sub_routine = 0
    cur_index = 0

    # to speed up, it tries to match by the step of the quarter of clip length
    # because distance gets smaller near the matching part
    # at the other parts, it doesn't check one by one, skips them
    for i in range(0, len(src), half_of_cpm_width):
        if i + half_of_cpm_width < len(src):
            sub_routine = half_of_cpm_width
        else:
            sub_routine = len(src) - 1 - i
        for m in range(sub_routine):
            cur_index = i + m
            temp = []

            # compare source and split fingerprints
            # by extracting same size of values as splitter
            for j in range(cmp_width):
                if cur_index + j > len(src) - 1:
                    break
                for k in range(len(src[cur_index + j])):
                    temp.append([j, src[cur_index + j][k]])

            if len(temp) == 0:  # if no matched values are given
                continue

            # calculate euclidean distance based on fast DTW algorithm
            distance, path = fastdtw(dest, temp, dist=euclidean)
            distance_list.append(distance)
            if distance < DISTANCE_LIMIT:
                is_consecutive = True
                d_pairs.append(distance)
                t_pairs.append(start_ms + cur_index * unit_ms)
            else:
                # add consecutive values in the same list
                # e.g. [[[da1, da2], [ta1, ta2]], [[db1, db2], [tb1, tb2]], ...]
                if is_consecutive:
                    is_consecutive = False
                    dist_pairs.append([d_pairs, t_pairs])
                    d_pairs = []
                    t_pairs = []
                break

    # get min distance and time among consecutive values
    # add them ret list
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

    if len(ret):
        split_points.extend(ret)

    print('<<< Thread {}'.format(thread_id))


def _fingerprint(data, plot=False):
    """
    This get spectrum of input array and get local
    maximum values.
    :param data: 2-d array data
    :param plot: show plot
    :return: local maxima list
    """

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
    """
    This retrieves local peak points list of
    each segment of frequency.
    :param arr2D: 2-d array data
    :param plot: show plot
    :return: the list of peak points list
    """

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
    """
    This converts input audio file into mono wave file
    with frequency of 44.1K
    :param file: input file
    :return: converted file name
    """

    if not os.path.exists(file):
        print('No such input file...')
        print('Invalid path: {}'.format(file))
        return False
    else:
        print('Input file exists.')

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

    if not os.path.exists(converted_file):
        print('No temp.wav file...')
        return False
    else:
        print('temp.wav file exists.')

    return converted_file
