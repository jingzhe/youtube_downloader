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
    iFile = 0;
    httpreply = 0;
    downloadreply = 0;
    iDownloadProgress = 0;
}

FileDownloader::~FileDownloader()
{
    delete iFile;
    delete httpreply;
    delete downloadreply;
}

QString FileDownloader::getInfoText()
{
    return iInfoText;
}

int FileDownloader::getDownloadProgress()
{
    return iDownloadProgress;
}

int FileDownloader::getDownloadState()
{
    return iState;
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
        iInfoText += tr("start getting info ") + uri + "\n";
    }
    else
    {
        iState = EReady;
        iInfoText += tr("download failed\n");
    }
    emit downloadStateChanged();
    emit infoTextChanged();
    return 0;
}

void FileDownloader::httpFinished()
{
    if (iGettingVideoInfoAborted)
    {
        httpreply->deleteLater();
        httpreply = 0;
        iDownloadProgress = 0;
        emit downloadProgressChanged();
        iState = EReady;
        emit downloadStateChanged();
        iInfoText += tr("download canceled\n");
        emit infoTextChanged();
        return;
    }
    if(iFullInfo.indexOf("token") == -1)
    {
        httpreply->deleteLater();
        httpreply = 0;
        iDownloadProgress = 0;
        emit downloadProgressChanged();
        iState = EReady;
        emit downloadStateChanged();

        if(el_type == "embedded")
            el_type = "detailpage";
        else if(el_type == "detailpage")
            el_type = "vevo";
        else
        {
            iInfoText += tr("download failed\n");
            emit infoTextChanged();
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
        	emit downloadStateChanged();
        	iInfoText += tr("start getting info ") + iId + "\n";

		}
		else
		{
            iState = EReady;
        	emit downloadStateChanged();
        	iInfoText += tr("download failed ") + iId + "\n";			
		}
	    emit infoTextChanged();
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
        if(myIndex != -1 && myIndex <= index)
        {
            index = myIndex;
            urlIndex++;
        }
    }
    if(urlIndex == -1)
    {
        httpreply->deleteLater();
        httpreply = 0;
        iDownloadProgress = 0;
        emit downloadProgressChanged();
        iState = EReady;
        emit downloadStateChanged();
        iInfoText += tr("download failed\n");
        emit infoTextChanged();
        return;
    }
    QString correct = strlist.at(urlIndex);;
    QUrl correctUrl("?" + correct);
    QByteArray correctArray = correctUrl.encodedQueryItemValue("url");
    QString correctAddress = QUrl::fromPercentEncoding(correctArray);
    QByteArray finalArray;
    finalArray.append(correctAddress);
    QString finalAddr = QUrl::fromPercentEncoding(finalArray);
    QByteArray sigArray = correctUrl.encodedQueryItemValue("sig");
    QString signature = QUrl::fromPercentEncoding(sigArray);

    httpreply->deleteLater();
    httpreply = 0;

    //open the file
    QString home = settings->value("output_path").toString();
    QString outputFile = home + QDir::separator() + iId + ".flv";
    iFile = new QFile(outputFile);
    if(!iFile->open(QIODevice::WriteOnly))
    {
        iState = EReady;
        iInfoText += tr("download cancelled");
        emit downloadStateChanged();
        emit infoTextChanged();
        delete iFile;
        iFile = NULL;
        return;
    }


    qDebug() << "download started" << endl;
    QByteArray temp1;
    temp1.append(finalAddr);
    finalAddr = QUrl::fromPercentEncoding(temp1) + "&signature=" + signature;;

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
        iInfoText += tr("start download video file \n");
        emit infoTextChanged();
        iState = EDownloading;
        emit downloadStateChanged();
    }
    else
    {
        delete iFile;
        iFile = NULL;
        iDownloadProgress = 0;
        emit downloadProgressChanged();
        iState = EReady;
        emit downloadStateChanged();
        iInfoText += tr("download failed\n");
        emit infoTextChanged();
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
        iDownloadProgress = 0;
        emit downloadProgressChanged();
        iState = EReady;
        emit downloadStateChanged();
        iInfoText += tr("download canceled\n");
        emit infoTextChanged();
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
    emit downloadStateChanged();
    iInfoText += tr("\ndownload finished\n");
    emit infoTextChanged();

}

void FileDownloader::downloadReadyRead()
{
    //qDebug() << "download ready read" << endl;
    if (iFile)
        iFile->write(downloadreply->readAll());

    iInfoText += tr(".");
    emit infoTextChanged();
}

void FileDownloader::updateDataReadProgress(qint64 bytesRead, qint64 totalBytes)
{
    //qDebug() << "updateDataReadProgress bytesread" << bytesRead << "totalBytes:" << totalBytes << endl;
    if(totalBytes > 0)
    {
        iDownloadProgress = bytesRead * 100 / totalBytes;
        emit downloadProgressChanged();
    }
}

int FileDownloader::cancelDownload()
{
    if(iState == EGettingVideoInfo)
    {
        iInfoText += tr("cancel getting video info\n");
        emit infoTextChanged();
        iGettingVideoInfoAborted = true;
        httpreply->abort();
    }
    else if(iState == EDownloading)
    {
        iInfoText += tr("\ncancel downloading\n");
        emit infoTextChanged();
        iDownloadRequestAborted = true;
        downloadreply->abort();

    }
    return 0;
}

int FileDownloader::clearInfo()
{
    iInfoText.clear();
    emit infoTextChanged();

    return 0;
}

QString FileDownloader::getOutputPath()
{
    return settings->value("output_path").toString();
}

QString FileDownloader::getProxyAddress()
{
    return settings->value("proxy_host").toString();
}

QString FileDownloader::getPortNumber()
{
    return settings->value("proxy_port").toString();
}

QString FileDownloader::getUseProxy()
{
    return settings->value("use_proxy").toString();
}

int FileDownloader::saveSettings(const QString& outputPath,
                 const QString& useProxy,
                 const QString& proxyAddr,
                 const QString& portNumber)
{
    settings->setValue("proxy_host", QVariant(proxyAddr));
    settings->setValue("proxy_port", QVariant(portNumber));
    settings->setValue("output_path", QVariant(outputPath));
    settings->setValue("use_proxy", QVariant(useProxy));

    return 0;
}

