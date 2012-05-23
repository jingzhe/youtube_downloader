#include <QNetworkRequest>
#include <QDebug>
#include <QUrl>
#include <QDir>
#include <QNetworkCookieJar>
#include "filedownloader.h"


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

    proxy.setType(QNetworkProxy::HttpProxy);
    proxy.setHostName(tr("192.168.220.5"));
    proxy.setPort(8080);
    iManager = new QNetworkAccessManager(this);
    //iManager->setProxy(proxy);
    //iManager->setCookieJar(new QNetworkCookieJar(iManager));
    iFullInfo = "?"; //hack
}

int FileDownloader::download(const QString& uri)
{
    iState = EDownloading;
    iDownloadRequestAborted = false;
    iId = uri;
    QString fulluri = QString("http://www.youtube.com/get_video_info?&video_id=%1&el=embedded&ps=default&eurl=&gl=US&hl=en").arg(uri);
    QNetworkRequest request(fulluri);
    httpreply = iManager->get(request);
    connect(httpreply, SIGNAL(finished()), this, SLOT(httpFinished()));
    connect(httpreply, SIGNAL(readyRead()), this, SLOT(httpReadyRead()));
    emit stateChanged(iState);

    return 0;
}

void FileDownloader::httpFinished()
{
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
    QString correct = strlist.at(urlIndex);;
    QUrl correctUrl("?" + correct);
    QByteArray correctArray = correctUrl.encodedQueryItemValue("url");
    QString correctAddress = QUrl::fromPercentEncoding(correctArray);
    QByteArray finalArray;
    finalArray.append(correctAddress);
    iFinalAddr = QUrl::fromPercentEncoding(finalArray);

    httpreply->deleteLater();
    httpreply = 0;

    //open the file
    QString home = QDir::homePath();
    QString outputFile = home + QDir::separator() + iId + ".flv";
    iFile = new QFile(outputFile);
    if(!iFile->open(QIODevice::WriteOnly))
    {
        delete iFile;
        iFile = NULL;
        return;
    }


    qDebug() << "download started" << endl;
    //qDebug() << "iFinalAddr: " << iFinalAddr << endl;
    QByteArray temp1;
    temp1.append(iFinalAddr);
    iFinalAddr = QUrl::fromPercentEncoding(temp1);
    //qDebug() << "newAddr: " << iFinalAddr << endl;

    //start to download
    QUrl downloadUrl(iFinalAddr);
    QNetworkRequest request(downloadUrl);
    downloadreply = iManager->get(request);
    connect(downloadreply, SIGNAL(finished()), this, SLOT(downloadFinished()));
    connect(downloadreply, SIGNAL(readyRead()), this, SLOT(downloadReadyRead()));
    connect(downloadreply, SIGNAL(downloadProgress(qint64,qint64)),
            this, SLOT(updateDataReadProgress(qint64,qint64)));



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
        return;
    }
    qDebug() << "downloadFinished" << endl;

    iFile->flush();
    iFile->close();


    if (downloadreply->error())
    {
        qDebug() << "error is " << downloadreply->error() << endl;
        iFile->remove();
        //downloadButton->setEnabled(true);
    }
    else
    {
        //downloadButton->setEnabled(true);
    }

    downloadreply->deleteLater();
    downloadreply = 0;
    delete iFile;
    iFile = 0;
    iState = EReady;
    emit stateChanged(iState);

}

void FileDownloader::downloadReadyRead()
{
    //qDebug() << "download ready read" << endl;
    if (iFile)
        iFile->write(downloadreply->readAll());
}

void FileDownloader::updateDataReadProgress(qint64 bytesRead, qint64 totalBytes)
{
    //qDebug() << "updateDataReadProgress bytesread" << bytesRead << "totalBytes:" << totalBytes << endl;
    int value = bytesRead * 100 / totalBytes;
    emit downloadProgress(value);
}

int FileDownloader::cancelDownload()
{
    if(iState == EDownloading)
    {
        qDebug() << "cancel download" << endl;
        iDownloadRequestAborted = true;
        downloadreply->abort();
    }
    return 0;
}

DownloadState FileDownloader::state()
{
    return iState;
}
