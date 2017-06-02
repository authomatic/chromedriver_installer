FROM library/python

WORKDIR /home/chromedriver_installer

ADD . /home/chromedriver_installer

RUN apt-get -y update
RUN apt-get -y install libnss3 libgconf-2-4
RUN pip install -r requirements.txt

CMD tox