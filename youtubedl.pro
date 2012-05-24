#-------------------------------------------------
#
# Project created by QtCreator 2012-05-16T15:25:56
#
#-------------------------------------------------

QT       += core gui network

TARGET = youtubedl
TEMPLATE = app


SOURCES += main.cpp\
        mainwindow.cpp \
    filedownloader.cpp \
    infoextractor.cpp \
    youtubeie.cpp \
    audioextractor.cpp

HEADERS  += mainwindow.h \
    filedownloader.h \
    infoextractor.h \
    youtubeie.h \
    audioextractor.h

FORMS    += mainwindow.ui
