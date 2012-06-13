// import QtQuick 1.0 // to target S60 5th Edition or Maemo 5
import QtQuick 1.1

Rectangle {
    width: 450
    height: 220
    radius: 5
    border.width: 2; border.color: "gray"
    property alias text: textDisplay.text

    Flickable {
        id: flicable
        anchors.fill: parent
        contentWidth: width
        contentHeight: textDisplay.height
        clip: true

        Text {
            id: textDisplay
            width: 450
            //anchors.centerIn: parent
            font.pixelSize: 12
            wrapMode: Text.WrapAnywhere
        }
    }
}
