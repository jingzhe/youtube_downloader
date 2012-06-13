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
    EReady = 0,
    EGettingVideoInfo,
    EDownloading
};

class FileDownloader : public QObject
{
    Q_OBJECT

public:
    explicit FileDownloader(QObject *parent = 0);
    ~FileDownloader();

public:
    Q_PROPERTY(QString infoText READ getInfoText NOTIFY infoTextChanged)
    QString getInfoText();

    Q_PROPERTY(int downloadProgress READ getDownloadProgress NOTIFY downloadProgressChanged)
    int getDownloadProgress();

    Q_PROPERTY(int downloadState READ getDownloadState NOTIFY downloadStateChanged)
    int getDownloadState();

signals:
    void infoTextChanged();
    void downloadProgressChanged();
    void downloadStateChanged();

public slots:
    int download(const QString& uri);
    int cancelDownload();
    int clearInfo();
    QString getOutputPath();
    QString getProxyAddress();
    QString getPortNumber();
    QString getUseProxy();
    int saveSettings(const QString& outputPath,
                     const QString& useProxy,
                     const QString& proxyAddr,
                     const QString& portNumber);

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

    QString iInfoText;
    int iDownloadProgress;

};

#endif // FILEDOWNLOADER_H
