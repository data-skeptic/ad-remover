FROM ubuntu:18.04
RUN apt-get update
RUN apt-get install -y ffmpeg
RUN apt-get install -y software-properties-common
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt-get install -y python3.7
RUN apt-get install -y wget
RUN apt-get install -y python3-pip

RUN pip3 install numpy
RUN pip3 install pandas
RUN pip3 install boto3
RUN pip3 install dateparser
RUN pip3 install python-dotenv
RUN pip3 install matplotlib
RUN pip3 install cycler
RUN pip3 install fastdtw
RUN pip3 install kiwisolver
RUN pip3 install pydub
RUN pip3 install pyparsing
RUN pip3 install python-dateutil
RUN pip3 install scipy
RUN pip3 install wget
RUN pip3 install boto3
RUN pip3 install awscli
#RUN pip3 install glob

WORKDIR /app
ADD . /app

ENTRYPOINT ["python3", "main.py"]
