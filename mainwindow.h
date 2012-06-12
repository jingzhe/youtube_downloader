#ifndef MAINWINDOW_H
#define MAINWINDOW_H

#include <QMainWindow>
#include "filedownloader.h"
#include "audioextractor.h"

namespace Ui {
class MainWindow;
}

class MainWindow : public QMainWindow
{
    Q_OBJECT
    
public:
    explicit MainWindow(QWidget *parent = 0);
    ~MainWindow();

public slots:
    void startDownload();
    void cancelDownload();
    void updateProgress(int value);
    void stateChanged(DownloadState state);
    void closeApp();
    void extractAudio();
    void infoChanged(const QString& text);
    void clearInfoText();
    void openSettings();
    void openAbout();
    void extractStateChanged(int state);
    void codecInfo();
    void encodeX264();
    
private:
    Ui::MainWindow *ui;
    FileDownloader* iDownloader;
    AudioExtractor* iAudioExtractor;
    bool iTrytoClose;
};

#endif // MAINWINDOW_H
