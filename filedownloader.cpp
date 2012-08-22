#include <QNetworkRequest>
#include <QDebug>
#include <QUrl>
#include <QDir>
#include <QNetworkCookieJar>
#include <QVariant>
#include "filedownloader.h"

const QString VIDEO_INFO_URI = QString("http://www.youtube.com/get_video_info?&video_id=%1&el=%2&ps=default&eurl=&gl=US&hl=en");

FileDownloader::FileDownloader(QObject *parent) :
    QObject(parent)
{
    iAvailable_formats.append("38");
    iAvailable_formats.append("37");
    iAvailable_formats.append("22");
    iAvailable_formats.append("45");
    iAvailable_formats.append("35");
    iAvailable_formats.append("44");
    iAvailable_formats.append("34");
    iAvailable_formats.append("18");
    iAvailable_formats.append("43");
    iAvailable_formats.append("6");
    iAvailable_formats.append("5");
    iAvailable_formats.append("17");
    iAvailable_formats.append("13");
    iState = EReady;

    settings = new QSettings("mycompany", "youtubedl", this);
    QString hostAddr = settings->value("proxy_host").toString();
    if(hostAddr.isEmpty())
    {
        settings->setValue("proxy_host", QVariant("192.168.220.5"));
    }
    QString port = settings->value("proxy_port").toString();
    if(port.isEmpty())
    {
        settings->setValue("proxy_port", QVariant("8080"));
    }
    QString home = settings->value("output_path").toString();
    if(home.isEmpty())
    {
        QString t = QDir::homePath();
        settings->setValue("output_path", QVariant(t));
    }
    iManager = new QNetworkAccessManager(this);
    iFullInfo = "?"; //hack
    el_type = "embedded";
}

FileDownloader::~FileDownloader()
{
    delete iFile;
    delete httpreply;
    delete downloadreply;
}

int FileDownloader::download(const QString& uri)
{
    if(iManager->networkAccessible() != QNetworkAccessManager::Accessible)
    {
        delete iManager;
        iManager = new QNetworkAccessManager(this);
    }
    QString checkStr = settings->value("use_proxy").toString();
    if(checkStr == "1")
    {
        QString hostAddr = settings->value("proxy_host").toString();
        QString port = settings->value("proxy_port").toString();
        proxy.setType(QNetworkProxy::HttpProxy);
        proxy.setHostName(hostAddr);
        proxy.setPort(port.toInt());
        iManager->setProxy(proxy);;
    }
    else
    {
        iManager->setProxy(emptyProxy);
    }

    iState = EGettingVideoInfo;
    iGettingVideoInfoAborted = false;
    iDownloadRequestAborted = false;
    iId = uri;
    iFullInfo = "?"; //hack
    QString fulluri = VIDEO_INFO_URI.arg(uri).arg(el_type);
    QNetworkRequest request(fulluri);
    httpreply = iManager->get(request);
    if(httpreply)
    {
        connect(httpreply, SIGNAL(finished()), this, SLOT(httpFinished()));
        connect(httpreply, SIGNAL(readyRead()), this, SLOT(httpReadyRead()));
        emit stateChanged(iState);
        emit infoChanged(tr("start getting info ") + uri);
    }
    else
    {
        iState = EReady;
        emit stateChanged(iState);
        emit infoChanged(tr("download failed\n"));
    }
    return 0;
}

void FileDownloader::httpFinished()
{
    if (iGettingVideoInfoAborted)
    {
        httpreply->deleteLater();
        httpreply = 0;
        emit downloadProgress(0);
        iState = EReady;
        emit stateChanged(iState);
        emit infoChanged(tr("download canceled"));
        return;
    }
    if(iFullInfo.indexOf("token") == -1)
    {
        httpreply->deleteLater();
        httpreply = 0;
        emit downloadProgress(0);
        iState = EReady;
        emit stateChanged(iState);

        if(el_type == "embedded")
            el_type = "detailpage";
        else if(el_type == "detailpage")
            el_type = "vevo";
        else
        {
            emit infoChanged(tr("download failed"));
            return;
        }
        QString fulluri = VIDEO_INFO_URI.arg(iId).arg(el_type);
        QNetworkRequest request(fulluri);
        httpreply = iManager->get(request);
        if(httpreply)
        {
            connect(httpreply, SIGNAL(finished()), this, SLOT(httpFinished()));
            connect(httpreply, SIGNAL(readyRead()), this, SLOT(httpReadyRead()));
            iState = EGettingVideoInfo;
            iGettingVideoInfoAborted = false;
            iDownloadRequestAborted = false;
            emit stateChanged(iState);
            emit infoChanged(tr("start getting info ") + iId);
        }
        else
        {
            iState = EReady;
            emit stateChanged(iState);
            emit infoChanged(tr("download failed\n"));
        }
        return;
    }
    QUrl url(iFullInfo);
    QByteArray bytearray = url.encodedQueryItemValue("url_encoded_fmt_stream_map");
    QString url_map = QUrl::fromPercentEncoding(bytearray);
    QByteArray newArray;
    newArray.append(url_map);
    QString new_map = QUrl::fromPercentEncoding(newArray);
    QStringList strlist = new_map.split(",", QString::SkipEmptyParts);
    QString item;
    int index = iAvailable_formats.count() - 1;
    int urlIndex = -1;
    foreach(item, strlist)
    {
        QUrl itemUrl("?"+item);
        QByteArray tagArray = itemUrl.encodedQueryItemValue("itag");
        QString tagstr = QString(tagArray);
        int myIndex = iAvailable_formats.indexOf(tagstr);
        if(myIndex <= index)
        {
            index = myIndex;
            urlIndex++;
        }
    }
    if(urlIndex == -1)
    {
        httpreply->deleteLater();
        httpreply = 0;
        emit downloadProgress(0);
        iState = EReady;
        emit stateChanged(iState);
        emit infoChanged(tr("download failed"));
        return;
    }
    QString correct = strlist.at(urlIndex);;
    QUrl correctUrl("?" + correct);
    QByteArray correctArray = correctUrl.encodedQueryItemValue("url");
    QString correctAddress = QUrl::fromPercentEncoding(correctArray);
    QByteArray finalArray;
    finalArray.append(correctAddress);
    QString finalAddr = QUrl::fromPercentEncoding(finalArray);

    httpreply->deleteLater();
    httpreply = 0;

    //open the file
    QString home = settings->value("output_path").toString();
    QString outputFile = home + QDir::separator() + iId + ".flv";
    iFile = new QFile(outputFile);
    if(!iFile->open(QIODevice::WriteOnly))
    {
        iState = EReady;
        emit stateChanged(iState);
        emit infoChanged(tr("download canceled"));
        delete iFile;
        iFile = NULL;
        return;
    }


    qDebug() << "download started" << endl;
    QByteArray temp1;
    temp1.append(finalAddr);
    finalAddr = QUrl::fromPercentEncoding(temp1);

    //start to download
    QUrl downloadUrl(finalAddr);
    QNetworkRequest request(downloadUrl);
    downloadreply = iManager->get(request);
    if(downloadreply)
    {
        connect(downloadreply, SIGNAL(finished()), this, SLOT(downloadFinished()));
        connect(downloadreply, SIGNAL(readyRead()), this, SLOT(downloadReadyRead()));
        connect(downloadreply, SIGNAL(downloadProgress(qint64,qint64)),
                this, SLOT(updateDataReadProgress(qint64,qint64)));
        emit infoChanged(tr("start download video file "));
        iState = EDownloading;
		emit stateChanged(iState);
    }
    else
    {
        delete iFile;
        iFile = NULL;
        emit downloadProgress(0);
        iState = EReady;
        emit stateChanged(iState);
        emit infoChanged(tr("download failed\n"));
    }
}

void FileDownloader::httpReadyRead()
{
    QString all = httpreply->readAll();
    iFullInfo += all;
}

void FileDownloader::downloadFinished()
{
    if (iDownloadRequestAborted)
    {
        qDebug() << "download aborted" << endl;
        if (iFile) {
            iFile->close();
            iFile->remove();
            delete iFile;
            iFile = 0;
        }
        downloadreply->deleteLater();
        downloadreply = 0;
        emit downloadProgress(0);
        iState = EReady;
        emit stateChanged(iState);
        emit infoChanged(tr("download canceled"));
        return;
    }
    qDebug() << "downloadFinished" << endl;

    iFile->flush();
    iFile->close();


    if (downloadreply->error())
    {
        qDebug() << "error is " << downloadreply->error() << endl;
        iFile->remove();
    }

    downloadreply->deleteLater();
    downloadreply = 0;
    delete iFile;
    iFile = 0;
    iState = EReady;
    emit stateChanged(iState);
    emit infoChanged(tr("download finished"));

}

void FileDownloader::downloadReadyRead()
{
    //qDebug() << "download ready read" << endl;
    if (iFile)
        iFile->write(downloadreply->readAll());

    emit infoChanged(tr("."));
}

void FileDownloader::updateDataReadProgress(qint64 bytesRead, qint64 totalBytes)
{
    //qDebug() << "updateDataReadProgress bytesread" << bytesRead << "totalBytes:" << totalBytes << endl;
    if(totalBytes > 0)
    {
        int value = bytesRead * 100 / totalBytes;
        emit downloadProgress(value);
    }
}

int FileDownloader::cancelDownload()
{
    if(iState == EGettingVideoInfo)
    {
        emit infoChanged(tr("cancel getting video info"));
        iGettingVideoInfoAborted = true;
        httpreply->abort();
    }
    else if(iState == EDownloading)
    {
        emit infoChanged(tr("cancel downloading"));
        iDownloadRequestAborted = true;
        downloadreply->abort();

    }
    return 0;
}

DownloadState FileDownloader::state()
{
    return iState;
}
