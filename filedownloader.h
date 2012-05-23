#ifndef FILEDOWNLOADER_H
#define FILEDOWNLOADER_H

#include <QObject>
#include <QNetworkAccessManager>
#include <QNetworkReply>
#include <QStringList>
#include <QFile>
#include <QNetworkProxy>

enum DownloadState
{
    EReady,
    EDownloading
};

class FileDownloader : public QObject
{
    Q_OBJECT
public:
    explicit FileDownloader(QObject *parent = 0);

    int download(const QString& uri);
    int cancelDownload();
    DownloadState state();
    
signals:
    void downloadProgress(int progress);
    void stateChanged(DownloadState state);
    
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
    QString iFinalAddr;
    QFile* iFile;
    QString iId;
    bool iDownloadRequestAborted;
    QNetworkProxy proxy;
    DownloadState iState;
    
};

#endif // FILEDOWNLOADER_H
