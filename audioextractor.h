#ifndef AUDIOEXTRACTOR_H
#define AUDIOEXTRACTOR_H

#include <QObject>

class AudioExtractor : public QObject
{
    Q_OBJECT
public:
    explicit AudioExtractor(QObject *parent = 0);
    int extractAudio();
    
signals:
    
public slots:

private:
    QString probeVideo();

private:

    QString iVideoFile;
    
};

#endif // AUDIOEXTRACTOR_H
