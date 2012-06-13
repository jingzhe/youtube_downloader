// import QtQuick 1.0 // to target S60 5th Edition or Maemo 5
import QtQuick 1.1

Rectangle {
    id: settingsView
    width: 400
    height: 400


    Text {
        id: outputLabel
        text: qsTr("Output path:")
        font.pixelSize: 12
        anchors { top: parent.top; topMargin: 30; left: parent.left; leftMargin: 10 }
    }

    MyLineInput {
        id: outputInput
        width: 300
        anchors { left: outputLabel.right; leftMargin: 10; top: parent.top; topMargin: 20}
        focus: true
        text: getOutputPath()
    }

    Checkbox {
        id: proxyCheck
        width: 80
        height: 30
        text: "Use proxy"
        anchors { left: parent.left; leftMargin: 30; top: outputLabel.bottom; topMargin: 40 }
        checked: getUseProxy() === "1"
        onClicked: {
            checked = !checked;
            if(checked) {
                addressInput.myEnabled = true;
                portInput.myEnabled = true;
            }
            else {
                addressInput.myEnabled = false;
                portInput.myEnabled = false;
            }

        }
    }

    Text {
        id: addressLabel
        text: qsTr("Proxy address:")
        font.pixelSize: 12
        anchors { top: proxyCheck.bottom; topMargin: 30; left: parent.left; leftMargin: 40 }
    }

    MyLineInput {
        id: addressInput
        width: 250
        anchors { left: addressLabel.right; leftMargin: 10; top: proxyCheck.bottom; topMargin: 20}
        text: getProxyAddress()
        myEnabled: proxyCheck.checked
    }

    Text {
        id: portLabel
        text: qsTr("Proxy port:")
        font.pixelSize: 12
        anchors { top: addressLabel.bottom; topMargin: 50; left: parent.left; leftMargin: 40 }
    }

    MyLineInput {
        id: portInput
        width: 250
        anchors { left: portLabel.right; leftMargin: 10; top: addressInput.bottom; topMargin: 20}
        text: getPortNumber()
        myEnabled: proxyCheck.checked
    }

    MyPushButton {
        id: okButton
        width: 70
        anchors { right: cancelButton.left; rightMargin: 20; top: portInput.bottom; topMargin: 40 }
        text: "Ok"
        onClicked: {
            var useProxy;
            if(proxyCheck.checked) {
                useProxy = "1";
            }
            else {
                useProxy = "0";
            }
            saveSettings(outputInput.text,
                         useProxy,
                         addressInput.text,
                         portInput.text);

            mainView.visible = 1
            settingsView.visible = 0
        }
    }

    MyPushButton {
        id: cancelButton
        width: 70
        anchors { right: parent.right; rightMargin: 20; top: portInput.bottom; topMargin: 40 }
        text: "Cancel"
        onClicked: {
            mainView.visible = 1
            settingsView.visible = 0

            //restore original value
            outputInput.text = getOutputPath();
            proxyCheck.checked = getUseProxy() === "1";
            addressInput.text = getProxyAddress();
            portInput.text = getPortNumber();
            addressInput.myEnabled = proxyCheck.checked;
            portInput.myEnabled = proxyCheck.checked;
        }
    }

    FocusScope {
        id: focus_scope1
        x: 21
        y: 115
        width: 371
        height: 141
    }
}
