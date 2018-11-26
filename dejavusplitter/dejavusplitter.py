import time
from .fingerprint import *


class DejavuSplitter:

    def __init__(self):
        print('init...')
        self.maxima_series = []  # maxima pattern of split audio
        self.stop_points = []  # the point list which are below distance limitation
        self.length = 0  # the duration of source audio file

    def fingerprint_file(self, file):
        """
        This fingerprints the file.
        :param file: full path of the file
        :return: the list of maximum values ([f1,f2...], [f1, f2...], ...)
        """

        self.maxima_series = fingerprint(file)

        if not self.maxima_series:
            return False

        print('maxima_series:', self.maxima_series)

        return True

    def recognize_file(self, file):
        """
        This fingerprints the source file and compare each segments with
        audio clip file (self.maxima_series).
        :param file: source audio file full path
        :return: the list of [distance, time(ms)], the duration of audio
        """

        self.stop_points, self.length = recognize(file, self.maxima_series)

        if not self.stop_points:
            return False

        print('stop_points:', self.stop_points, ', length:', self.length)

        return True

    def split(self, src, splitter):
        print('splitter audio fingerprinting...')

        st1 = time.time()
        ff = self.fingerprint_file(splitter)
        print('fingerprint time:', time.time() - st1, '(s)')

        if not ff:
            return False

        print('source audio fingerprinting...')

        st1 = time.time()
        rf = self.recognize_file(src)
        print('recognition time:', time.time() - st1, '(s)')

        if not rf:
            return False

        print('splitting audio file...')
        st1 = time.time()
        self._split(src)
        print('split time:', time.time() - st1, '(s)')

    def _split(self, file):
        """
        This splits the source audio file accroding to stop points time.
        The time series are made by choosing time values from stop points list.
        :param file: the full path of the file
        :return: splitted audio files in original folder
        """

        ext_index = str(file).rindex('.')
        file_name = file[:ext_index]  # get the file name from the full path
        extension = file[ext_index + 1:]  # get the extension from the full path

        # extract time of all matched points
        time_series = [int(row[1] / 1000) for row in self.stop_points]
        time_series = [0] + time_series + [int(self.length / 1000)]
        print('time_series:', time_series)

        # split the source audio
        for i in range(1, len(time_series)):
            print('from', time_series[i - 1], 'to', time_series[i])

            cmd = 'ffmpeg -i {} -acodec copy -ss {} -to {} {}_{}.{}'.format(file, time_series[i - 1], time_series[i],
                                                                            file_name, i, extension)

            print(cmd)

            proc = subprocess.Popen(cmd, shell=True)
            proc.communicate()
            print('convert is done...')

    # remove temp file
    if os.path.exists('temp.wav'):
        os.remove('temp.wav')
