// import QtQuick 1.0 // to target S60 5th Edition or Maemo 5
import QtQuick 1.1

Rectangle {
    width: 400
    height: 400
    Text {
        id: videoIdLabel
        text: qsTr("Video Id:")
        anchors { top: parent.top; topMargin: 20; left: parent.left; leftMargin: 10 }
    }

    MyLineInput {
        id: videoIdInput
        anchors { left: videoIdLabel.right; top: parent.top; right: parent.right; margins: 10;}
        focus: true
    }

    Text {
        id: progressLabel
        text: qsTr("Progress:")
        anchors { top: videoIdLabel.bottom; topMargin: 30; left: parent.left; leftMargin: 10 }
    }

    Rectangle {
        id: progressBackground
        height: 30
        border.width: 2
        border.color: "gray"
        color: "lightgray"
        radius: 5
        anchors { top: videoIdInput.bottom; topMargin: 10;
            left: progressLabel.right; leftMargin: 10 ;
            right: parent.right; rightMargin: 10
        }
    }


    Rectangle {
        id: progressFrontground
        width: 120
        height: 30
        border.width: 2
        color: "red"
        radius: 5
        anchors { top: videoIdInput.bottom; topMargin: 10;
            left: progressLabel.right; leftMargin: 10; }
    }

    TextDisplay {
        id: resultText
        anchors { top: progressBackground.bottom; topMargin: 10;
            left: parent.left; leftMargin: 10;
            right: parent.right; rightMargin: 10
        }
        text: "result"
    }

    MyPushButton {
        id: startButton
        width: 70
        anchors { left: parent.left; leftMargin: 20; top: resultText.bottom; topMargin: 20 }
        text: "Start"
        onClicked: {
        }
    }

    MyPushButton {
        id: cancelButton
        width: 70
        anchors { left: startButton.right; leftMargin: 60; top: resultText.bottom; topMargin: 20 }
        text: "Cancel"
        onClicked: {
        }
    }

    MyPushButton {
        id: closeButton
        width: 70
        anchors { left: cancelButton.right; leftMargin: 60; top: resultText.bottom; topMargin: 20 }
        text: "Close"
        onClicked: {
            Qt.quit();
        }
    }

}
