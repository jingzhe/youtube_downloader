#include <QtGui/QApplication>
#include <QDeclarativeEngine>
#include <QDeclarativeContext>
#include "qmlapplicationviewer.h"
#include "filedownloader.h"

Q_DECL_EXPORT int main(int argc, char *argv[])
{
    QScopedPointer<QApplication> app(createApplication(argc, argv));

    QmlApplicationViewer viewer;
    FileDownloader fileDownloader;
    viewer.engine()->rootContext()->setContextObject(&fileDownloader);
    viewer.setOrientation(QmlApplicationViewer::ScreenOrientationAuto);
    viewer.setMainQmlFile(QLatin1String("qml/qmldownload/Loader.qml"));
    viewer.showExpanded();

    return app->exec();
}
