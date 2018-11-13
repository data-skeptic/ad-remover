from .fingerprint import *


class DejavuSplitter:

    def __init__(self):
        print('init...')
        self.maxima_series = []
        self.stop_points = []
        self.length = 0

    def fingerprint_file(self, file):
        self.maxima_series = fingerprint(file)
        print('maxima_series:', self.maxima_series)

    def recognize_file(self, file):
        self.stop_points, self.length = recognize(file, self.maxima_series)
        print('stop_points:', self.stop_points, ', length:', self.length)

    def split(self, src, splitter):
        print('splitter audio fingerprinting...')
        self.fingerprint_file(splitter)

        print('source audio fingerprinting...')
        self.recognize_file(src)

        print('splitting audio file...')
        self._split(src)

    def _split(self, file):
        ext_index = str(file).rindex('.')
        file_name = file[:ext_index]
        extension = file[ext_index + 1:]

        time_series = [int(row[1] / 1000) for row in self.stop_points]
        time_series = [0] + time_series + [int(self.length / 1000)]
        print('time_series:', time_series)

        for i in range(1, len(time_series)):
            cmd = 'ffmpeg -ss {} -i {} -to {} -c copy {}_{}.{}'.format(time_series[i - 1], file,
                                                                       time_series[i], file_name, i,
                                                                       extension)

            try:
                proc = subprocess.Popen(cmd)
                proc.communicate()
                print('convert is done...')
            except:
                print('raised exception while converting...')

        if os.path.exists('temp.wav'):
            os.remove('temp.wav')
