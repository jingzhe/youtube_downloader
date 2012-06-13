// import QtQuick 1.0 // to target S60 5th Edition or Maemo 5
import QtQuick 1.1

Item {
    id: container
    width: 80; height: 30

    property alias text: label.text
    property bool checked: false
    signal clicked()

    Row {
        spacing: 5

        Image {
            //anchors.verticalCenter:  parent.verticalCenter
            //opacity: container.checked ? 1.0 : 0.01
            smooth: true
            width: 12; height: 12
            source:  container.checked ? "checked.png":"unchecked.png"
        }

        Text {
            id: label
            font.pixelSize: 14
        }
    }

    MouseArea {
        id: mouseArea
        anchors.fill: parent
        onClicked: { container.clicked(); }
    }
}
