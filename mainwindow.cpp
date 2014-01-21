#include <QScrollBar>
#include <QMessageBox>
#include "mainwindow.h"
#include "settingsdialog.h"
#include "ui_mainwindow.h"

MainWindow::MainWindow(QWidget *parent) :
    QMainWindow(parent),
    ui(new Ui::MainWindow)
{
    iTrytoClose = false;
    iDownloader = new FileDownloader(this);
    iAudioExtractor = new AudioExtractor(this);
    ui->setupUi(this);
    ui->progressBar->setMinimum(0);
    ui->progressBar->setMaximum(100);
    ui->progressBar->setValue(0);
    connect(ui->startButton, SIGNAL(clicked()), this, SLOT(startDownload()));
    connect(ui->cancelButton, SIGNAL(clicked()), this, SLOT(cancelDownload()));
    connect(iDownloader, SIGNAL(downloadProgress(int)), this, SLOT(updateProgress(int)));
    connect(iDownloader, SIGNAL(stateChanged(DownloadState)), this, SLOT(stateChanged(DownloadState)));
    connect(ui->extractButton, SIGNAL(clicked()), this, SLOT(extractAudio()));
    connect(ui->codecButton, SIGNAL(clicked()), this, SLOT(codecInfo()));
    connect(ui->encodeButton, SIGNAL(clicked()), this, SLOT(encodeX264()));
    connect(ui->closeButton, SIGNAL(clicked()), this, SLOT(closeApp()));
    connect(iDownloader, SIGNAL(infoChanged(const QString&)), this, SLOT(infoChanged(const QString&)));
    connect(ui->clearButton, SIGNAL(clicked()), this, SLOT(clearInfoText()));
    connect(ui->actionSettings, SIGNAL(triggered()), this, SLOT(openSettings()));
    connect(ui->actionAbout, SIGNAL(triggered()), this, SLOT(openAbout()));
    connect(iAudioExtractor, SIGNAL(infoChanged(const QString&)), this, SLOT(infoChanged(const QString&)));
    connect(iAudioExtractor, SIGNAL(extractStateChanged(int)), this, SLOT(extractStateChanged(int)));
    connect(iAudioExtractor, SIGNAL(encodeStateChanged(int)), this, SLOT(extractStateChanged(int)));
    ui->videoIdEdit->setText("nVjsGKrE6E8");
}

MainWindow::~MainWindow()
{
    delete ui;
}

void MainWindow::startDownload()
{
    QString id = ui->videoIdEdit->text();
    iDownloader->download(id);
}

void MainWindow::cancelDownload()
{
    iDownloader->cancelDownload();
}

void MainWindow::updateProgress(int value)
{
    ui->progressBar->setValue(value);
}

void MainWindow::stateChanged(DownloadState state)
{
    ui->startButton->setEnabled(state == EReady);
    if(state == EReady && iTrytoClose)
    {
        close();
    }
}

void MainWindow::closeApp()
{
    if(iDownloader->state() != EReady)
    {
        iTrytoClose = true;
        iDownloader->cancelDownload();
    }
    else
    {
        close();
    }
}

void MainWindow::extractAudio()
{
    iAudioExtractor->extractAudio(ui->videoIdEdit->text());
}

void MainWindow::infoChanged(const QString& text)
{
    if(text == ".")
        ui->infoEdit->insertPlainText(text);
    else
        ui->infoEdit->append(text);

    QScrollBar *sb = ui->infoEdit->verticalScrollBar();
    sb->setValue(sb->maximum());
}

void MainWindow::clearInfoText()
{
    ui->infoEdit->clear();
}

void MainWindow::openSettings()
{
    SettingsDialog dlg(this);
    dlg.exec();
}

void MainWindow::extractStateChanged(int state)
{
    this->setEnabled(state == 0);
}

void MainWindow::codecInfo()
{
    iAudioExtractor->codecInfo(ui->videoIdEdit->text());
}

void MainWindow::encodeX264()
{
    iAudioExtractor->encodeX264(ui->videoIdEdit->text());
}

void MainWindow::openAbout()
{
    QMessageBox msgBox;
    msgBox.setText("Author: Jingzhe Yu\nEmail: jingzhe.yu@gmail.com\n\nExtract mp3 and video encode need ffmpeg.\n\n");
    msgBox.exec();
}
