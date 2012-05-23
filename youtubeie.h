#ifndef YOUTUBEIE_H
#define YOUTUBEIE_H

#include "infoextractor.h"

class YoutubeIE : public InfoExtractor
{
    Q_OBJECT

public:
    explicit YoutubeIE(QObject *parent = 0);

signals:

public slots:

};

#endif // YOUTUBEIE_H

