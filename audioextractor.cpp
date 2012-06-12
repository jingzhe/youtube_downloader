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

void AudioExtractor::codecInfo(const QString& videoId)
{
    QString home = settings->value("output_path").toString();
    QString videoFile = home + QDir::separator() + videoId + ".flv";

    QString codecStr = "ffmpeg -i " + videoFile;
    connect(&codecProcess, SIGNAL(readyReadStandardError()), this, SLOT(showCodec()));
    codecProcess.start(codecStr);
}

void AudioExtractor::showCodec()
{
    QString result = codecProcess.readAllStandardError();
    int pos1 = result.indexOf("Metadata:");
    int pos2 = result.indexOf("At least");
    QString finalResult = result.mid(pos1, pos2 - pos1);
    emit infoChanged(finalResult);
}

void AudioExtractor::encodeX264(const QString& videoId)
{
    QString home = settings->value("output_path").toString();
    QString videoFile = home + QDir::separator() + videoId + ".flv";
    QString outputFile = home + QDir::separator() + videoId + ".mp4";
    connect(&encodeProcess, SIGNAL(finished(int,QProcess::ExitStatus)),
            this, SLOT(encodeFinished(int, QProcess::ExitStatus)));

    QString encodecStr = "ffmpeg -i " + videoFile + " -vcodec libx264 " + outputFile;
    encodeProcess.start(encodecStr);
    emit infoChanged(encodecStr);
    emit extractStateChanged(1);

}

void AudioExtractor::encodeFinished(int exitCode, QProcess::ExitStatus exitStatus)
{
    emit encodeStateChanged(0);
    if(exitCode != 0)
        emit infoChanged("failed to encode mp4");
    else
        emit infoChanged("succeeded to encode mp4");
}
