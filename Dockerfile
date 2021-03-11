FROM python:3.9.2-buster

LABEL maintainer="bultau@gmail.com"
ENV DEBIAN_FRONTEND noninteractive
ENV DEBCONF_NOWARNINGS yes

WORKDIR /opt/mattermost-rss
RUN apt-get update \
 && apt-get upgrade -y --no-install-recommends \
 && apt-get -y clean \
 && rm -rf /var/lib/apt/lists/*
RUN pip install requests pandas feedparser
