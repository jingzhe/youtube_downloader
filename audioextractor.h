#ifndef AUDIOEXTRACTOR_H
#define AUDIOEXTRACTOR_H

#include <QObject>
#include <QSettings>
#include <QProcess>

class AudioExtractor : public QObject
{
    Q_OBJECT
public:
    explicit AudioExtractor(QObject *parent = 0);
    int extractAudio(const QString& videoId);
    void codecInfo(const QString& videoId);
    
signals:
    void infoChanged(const QString& info);
    void extractStateChanged(int state);
    void encodeStateChanged(int state);
    
public slots:
    void extractFinished(int exitCode, QProcess::ExitStatus exitStatus);
    void encodeFinished(int exitCode, QProcess::ExitStatus exitStatus);
    void showCodec();
    void encodeX264(const QString& videoId);

private:
    QString probeVideo();

private:

    QString iVideoFile;
    QSettings* settings;
    QProcess extractProcess;
    QProcess codecProcess;
    QProcess encodeProcess;
    
};

#endif // AUDIOEXTRACTOR_H
