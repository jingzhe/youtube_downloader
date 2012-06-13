// import QtQuick 1.0 // to target S60 5th Edition or Maemo 5
import QtQuick 1.1

Rectangle {
    id: button
    width: 100
    height: 40
    radius: 5
    color: mouse.pressed && state == 0 ? "gray" : "lightgray"
    property alias text: buttonLabel.text
    property int state: 0
    signal clicked

    Text {
        id: buttonLabel
        anchors.centerIn: parent
        font.pixelSize: parent.height * .5
    }

    MouseArea {
        id: mouse
        anchors.fill: parent
        onClicked: button.clicked()
    }
}
