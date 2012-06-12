#ifndef FILEDOWNLOADER_H
#define FILEDOWNLOADER_H

#include <QObject>
#include <QNetworkAccessManager>
#include <QNetworkReply>
#include <QStringList>
#include <QFile>
#include <QNetworkProxy>
#include <QSettings>

enum DownloadState
{
    EReady,
    EGettingVideoInfo,
    EDownloading
};

class FileDownloader : public QObject
{
    Q_OBJECT
public:
    explicit FileDownloader(QObject *parent = 0);
    ~FileDownloader();


    int download(const QString& uri);
    int cancelDownload();
    DownloadState state();
    
signals:
    void downloadProgress(int progress);
    void stateChanged(DownloadState state);
    void infoChanged(const QString& info);
    
public slots:

private slots:
    void httpFinished();
    void httpReadyRead();
    void downloadFinished();
    void downloadReadyRead();
    void updateDataReadProgress(qint64 bytesRead, qint64 totalBytes);

private:
    QStringList iAvailable_formats;
    QNetworkAccessManager* iManager;
    QNetworkReply *httpreply;
    QNetworkReply *downloadreply;
    QString iFullInfo;
    QFile* iFile;
    QString iId;
    bool iGettingVideoInfoAborted;
    bool iDownloadRequestAborted;
    QNetworkProxy proxy;
    QNetworkProxy emptyProxy;
    DownloadState iState;
    QSettings* settings;
    QString el_type; //embedded, detailpage, vevo
    
};

#endif // FILEDOWNLOADER_H
