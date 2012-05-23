#ifndef MAINWINDOW_H
#define MAINWINDOW_H

#include <QMainWindow>
#include "filedownloader.h"

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
    
private:
    Ui::MainWindow *ui;
    FileDownloader* iDownloader;
    bool iTrytoClose;
};

#endif // MAINWINDOW_H
