#include <QFileDialog>
#include "settingsdialog.h"
#include "ui_settingsdialog.h"

SettingsDialog::SettingsDialog(QWidget *parent) :
    QDialog(parent),
    ui(new Ui::SettingsDialog)
{
    settings = new QSettings("mycompany", "youtubedl", this);
    ui->setupUi(this);
    connect(ui->browseButton, SIGNAL(clicked()), this, SLOT(openFileDlg()));
    connect(ui->buttonBox, SIGNAL(accepted()), this, SLOT(okToExit()));
    connect(ui->checkProxy, SIGNAL(clicked(bool)), ui->groupProxy, SLOT(setEnabled(bool)));
    ui->addressEdit->setText(settings->value("proxy_host").toString());
    ui->portEdit->setText(settings->value("proxy_port").toString());
    ui->outputEdit->setText(settings->value("output_path").toString());
    QString checkStr = settings->value("use_proxy").toString();
    if(checkStr == "1")
    {
        ui->checkProxy->setChecked(true);
    }
    else
    {
        ui->checkProxy->setChecked(false);
    }
    ui->groupProxy->setEnabled(ui->checkProxy->isChecked());
}

SettingsDialog::~SettingsDialog()
{
    delete ui;
}

void SettingsDialog::openFileDlg()
{
    QString outputDir = settings->value("output_path").toString();
    QString dir = QFileDialog::getExistingDirectory(this, tr("Select Directory"),
                                                    outputDir,
                                                    QFileDialog::ShowDirsOnly
                                                    | QFileDialog::DontResolveSymlinks);
    settings->setValue("output_path", QVariant(dir));
    ui->outputEdit->setText(dir);
}

void SettingsDialog::okToExit()
{
    QString addr = ui->addressEdit->text();
    settings->setValue("proxy_host", QVariant(addr));

    QString port = ui->portEdit->text();
    settings->setValue("proxy_port", QVariant(port));

    QString output = ui->outputEdit->text();
    settings->setValue("output_path", QVariant(output));

    QString useProxy;
    if(ui->checkProxy->isChecked())
        useProxy = "1";
    else
        useProxy = "0";
    settings->setValue("use_proxy", QVariant(useProxy));

    accept();
}
