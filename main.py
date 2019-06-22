import os
import wget
from pydub import AudioSegment
import boto3
import glob

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
    #
    bucketName = "dataskeptic.com"
    files = glob.glob(f'{SOURCE_PATH}/*_*.mp3')
    if len(files) != 3:
        print(files)
        for file in files:
            i = file.rfind('/')
            f = file[i+1:]
            s3key = f"_audio/noad/errors/{f}"
            print(s3key)
            s3 = boto3.client('s3', aws_access_key_id=os.environ['AWS_KEY'], aws_secret_access_key=os.environ['AWS_SECRET'])
            s3.upload_file(file, bucketName, s3key)
        raise Exception("Wrong number of files")
    f1 = files[0]
    f2 = files[2]
    s1 = AudioSegment.from_mp3(f1)
    s2 = AudioSegment.from_mp3(f2)
    result = s1 + s2
    fname = f1.replace("_1.", ".noad.")
    result.export(fname, format="mp3")
    y = datetime.now().year
    i = fname.rfind('/')
    f = fname[i+1:]
    s3key = f"_audio/noad/{y}/{f}"
    s3 = boto3.client('s3', aws_access_key_id=os.environ['AWS_KEY'], aws_secret_access_key=os.environ['AWS_SECRET'])
    s3.upload_file(fname, bucketName, s3key)


if __name__ == '__main__':
    splitter_url = os.environ['SPLITTER_SOUND_WAVE_URL']
    splitter = wget.download(splitter_url)
    os.rename(splitter, f'{SPLITTER_PATH}/{splitter}')
    #
    src_url = os.environ['SRC_MP3_URL']
    source = wget.download(src_url)
    os.rename(source, f'{SOURCE_PATH}/{source}')
    #
    main(source, splitter)
