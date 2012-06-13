// import QtQuick 1.0 // to target S60 5th Edition or Maemo 5
import QtQuick 1.1

Item {
    width: 480
    height: 400

    MainView {
        id: mainView
        visible: true
    }

    SettingsView {
        id: settingsView
        visible: false
    }
}
