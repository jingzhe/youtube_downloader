// import QtQuick 1.0 // to target S60 5th Edition or Maemo 5
import QtQuick 1.1

Rectangle {
    id: mainView
    width: 480
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
        text: "BzrI15uw92k"
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
        width: downloadProgress * progressBackground.width / 100
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
        text: infoText
    }

    MyPushButton {
        id: startButton
        width: 75
        anchors { left: parent.left; leftMargin: 15; top: resultText.bottom; topMargin: 20 }
        text: "Start"
        state: downloadState
        onClicked: {
            if(downloadState == 0) {
                download(videoIdInput.text)
            }
        }
    }

    MyPushButton {
        id: cancelButton
        width: 75
        anchors { left: startButton.right; leftMargin: 15; top: resultText.bottom; topMargin: 20 }
        text: "Cancel"
        onClicked: {
            cancelDownload();
        }
    }

    MyPushButton {
        id: clearButton
        width: 75
        anchors { left: cancelButton.right; leftMargin: 15; top: resultText.bottom; topMargin: 20 }
        text: "Clear"
        onClicked: {
            clearInfo();
        }
    }

    MyPushButton {
        id: settingsButton
        width: 75
        anchors { left: clearButton.right; leftMargin: 15; top: resultText.bottom; topMargin: 20 }
        text: "Settings"
        onClicked: {
            mainView.visible = 0
            settingsView.visible = 1
        }
    }

    MyPushButton {
        id: closeButton
        width: 75
        anchors { left: settingsButton.right; leftMargin: 15; top: resultText.bottom; topMargin: 20 }
        text: "Close"
        onClicked: {
            cancelDownload();
            Qt.quit();
        }
    }

}
