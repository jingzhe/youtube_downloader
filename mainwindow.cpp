#include "mainwindow.h"
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
    connect(ui->closeButton, SIGNAL(clicked()), this, SLOT(closeApp()));
    ui->videoIdEdit->setText("BzrI15uw92k");
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
    iAudioExtractor->extractAudio();
}

