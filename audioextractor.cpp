#include <QProcess>
#include <QDebug>
#include <QApplication>
#include <QCursor>
#include "audioextractor.h"

AudioExtractor::AudioExtractor(QObject *parent) :
    QObject(parent)
{
    iVideoFile = "/home/jingzhe/hrYnTRP_NQ8.flv";
}

int AudioExtractor::extractAudio()
{
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

    QString ffmpegStr = "ffmpeg -y -i /home/jingzhe/hrYnTRP_NQ8.flv -vn -acodec "
            + acodec + " /home/jingzhe/hrYnTRP_NQ8.mp3";
    qDebug() << ffmpegStr << endl;

    QProcess process;
    QApplication::setOverrideCursor(QCursor(Qt::WaitCursor));
    process.start(ffmpegStr);
    QString all;
    if (!process.waitForFinished(-1))
        qDebug() << "failed:" << process.errorString();
    else
        qDebug() << "succed" << endl;

    QApplication::restoreOverrideCursor();
    return 0;
}

QString AudioExtractor::probeVideo()
{
    QString all;
    QString result;
    QProcess process;
    QString probeStr = "ffprobe -show_streams " + iVideoFile;
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
