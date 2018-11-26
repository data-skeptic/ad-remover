import os

from dejavusplitter.dejavusplitter import DejavuSplitter

BASE_PATH = 'res'
SOURCE_PATH = os.path.join(BASE_PATH, 'source')
SPLITTER_PATH = os.path.join(BASE_PATH, 'splitter')


def main(src, splitter):
    src = os.path.join(SOURCE_PATH, src)
    splitter = os.path.join(SPLITTER_PATH, splitter)

    print(src)

    djv = DejavuSplitter()

    djv.split(src, splitter)


if __name__ == '__main__':
    src = 'full_episode.mp3'
    splitter = 'splice_sound.wav'
    main(src, splitter)
