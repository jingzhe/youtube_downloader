#include <QDebug>
#include <QApplication>
#include <QCursor>
#include <QDir>
#include "audioextractor.h"

AudioExtractor::AudioExtractor(QObject *parent) :
    QObject(parent)
{
    settings = new QSettings("mycompany", "youtubedl", this);
    connect(&extractProcess, SIGNAL(finished(int,QProcess::ExitStatus)),
            this, SLOT(extractFinished(int, QProcess::ExitStatus)));
}

int AudioExtractor::extractAudio(const QString& videoId)
{
    QString home = settings->value("output_path").toString();
    iVideoFile = home + QDir::separator() + videoId + ".flv";

    QString acodec;
    QString probeResult = probeVideo();
    if(probeResult == "mp3")
    {
        acodec = "copy";
    }
    else
    {
        acodec = "libmp3lame";
    }

    QString ffmpegStr = "ffmpeg -y -i " + iVideoFile + " -vn -acodec "
            + acodec + " " + home + QDir::separator() + videoId + ".mp3";
    emit infoChanged(ffmpegStr + "...");
    emit extractStateChanged(1);

    extractProcess.start(ffmpegStr);
    return 0;
}

QString AudioExtractor::probeVideo()
{
    QString all;
    QString result;
    QProcess process;
    QString probeStr = "ffprobe -show_streams " + iVideoFile;
    emit infoChanged(probeStr);
    process.start(probeStr);
    if (!process.waitForFinished())
        qDebug() << "failed:" << process.errorString();
    else
        all = process.readAll();

    QStringList list = all.split("\n");
    QString item;
    bool audioType = false;
    foreach(item, list)
    {
        if(item.startsWith("codec_name="))
        {
            result = item.split("=").at(1).trimmed();
        }
        else if(item.trimmed() == "codec_type=audio")
        {
            audioType = true;
        }

        if(audioType && !result.isEmpty())
        {
            return result;
        }
    }

    return result;
}

void AudioExtractor::extractFinished(int exitCode, QProcess::ExitStatus exitStatus)
{
    emit extractStateChanged(0);
    if(exitCode != 0)
        emit infoChanged("failed to extract mp3");
    else
        emit infoChanged("succeeded to extract mp3");
}
