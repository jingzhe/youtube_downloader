// import QtQuick 1.0 // to target S60 5th Edition or Maemo 5
import QtQuick 1.1

Rectangle {
    id:lineInput
    width: 100
    height: 40
    radius: 5
    border.width: 2
    signal clicked
    property alias text: inputText.text
    property bool myEnabled: true
    signal returned

    TextInput {
        id: inputText
        anchors.centerIn: parent
        width: parent.width - 16
        font.pixelSize: parent.height * .5
        focus: true
        readOnly: !myEnabled
        Keys.onReturnPressed: lineInput.returned()
    }

    MouseArea {
        anchors.fill: parent
        onClicked: {
            lineInput.clicked()
            inputText.focus = true
        }
    }
}
