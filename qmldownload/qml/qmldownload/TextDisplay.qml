// import QtQuick 1.0 // to target S60 5th Edition or Maemo 5
import QtQuick 1.1

Rectangle {
    width: 100
    height: 200
    radius: 5
    border.width: 2; border.color: "gray"

    property alias text: textDisplay.text

    Text {
        id: textDisplay
        height: parent.height - 8
        width: parent.width -16
        anchors.centerIn: parent
        font.pixelSize: 12
        wrapMode: Text.WordWrap
    }
}
