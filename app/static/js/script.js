class MessageBox {
    constructor(id, option) {
        this.id = id;
        this.option = option;
    }

    show(msg, type = "info", label = "CLOSE", callback = null) {
        if (this.id === null || typeof this.id === "undefined") {
            throw "Please set the 'ID' of the message box container.";
        }

        if (msg === "" || typeof msg === "undefined" || msg === null) {
            throw "The 'msg' parameter is empty.";
        }

        if (typeof label === "undefined" || label === null) {
            label = "CLOSE";
        }

        let msgboxArea = document.querySelector(this.id);
        let msgboxBox = document.createElement("DIV");
        let msgboxContent = document.createElement("DIV");
        let msgboxClose = document.createElement("A");
        let option = this.option

        if (msgboxArea === null) {
            throw "The Message Box container is not found.";
        }

        msgboxContent.classList.add("msgbox-content");
        msgboxContent.innerText = msg;

        msgboxClose.classList.add("msgbox-close");
        msgboxClose.setAttribute("href", "#");
        msgboxClose.innerText = label;

        msgboxBox.classList.add("msgbox-box");
        if (type === 'error') {
            msgboxBox.classList.add("error-box");
        } else if (type === 'success') {
            msgboxBox.classList.add("success-box");
        }
        msgboxBox.appendChild(msgboxContent);

        if (option.hideCloseButton === false
            || typeof option.hideCloseButton === "undefined") {
            msgboxBox.appendChild(msgboxClose);
        }

        msgboxArea.appendChild(msgboxBox);

        msgboxClose.addEventListener("click", (evt) => {
            evt.preventDefault();
            if (msgboxBox.classList.contains("msgbox-box-hide")) {
                // If the message box already have 'msgbox-box-hide' class
                // This is to avoid the appearance of exception if the close
                // button is clicked multiple times or clicked while hiding.
                return;
            }
            this.hide(msgboxBox, callback);
        });

        if (option.closeTime > 0) {
            this.msgboxTimeout = setTimeout(() => {
                this.hide(msgboxBox, callback);
            }, option.closeTime);
        }
    }

    hide(msgboxBox, callback) {
        if (msgboxBox !== null) {
            msgboxBox.classList.add("msgbox-box-hide");
        }

        msgboxBox.addEventListener("transitionend", () => {
            if (msgboxBox !== null) {
                msgboxBox.parentNode.removeChild(msgboxBox);
                clearTimeout(this.msgboxTimeout);

                if (callback !== null) {
                    callback();
                }
            }
        });
    }
}

let documentReady = function (fn) {
    if (document.readyState === "complete" || document.readyState === "interactive") {
        setTimeout(fn, 1);
    } else {
        document.addEventListener("DOMContentLoaded", fn);
    }
};

changeTab = function () {
    document.querySelectorAll('.page').forEach((elem) => {
        elem.className = 'page hide';
    })
    // noinspection JSUnresolvedVariable
    document.getElementById(this.id + '-page').className = 'page show';
    document.querySelectorAll('.selector').forEach((elem) => {
        elem.className = 'selector not-selected';
    });
    // noinspection JSUnresolvedVariable
    document.getElementById(this.id).className = 'selector selected';
};

changeForm = function () {
    document.querySelectorAll('.form-container').forEach((elem) => {
        elem.className = 'form-container hide';
    });
    document.querySelectorAll('.models-container').forEach((elem) => {
        elem.className = 'models-container hide';
    });
    document.querySelectorAll('.submit-container').forEach((elem) => {
        elem.className = 'submit-container hide';
    });
    // noinspection JSUnresolvedVariable
    if (this.checked) {
        document.querySelector('.slider-text').innerHTML = 'Parameter fields';
        document.getElementById('parameter-fields').className = 'form-container show';
        document.getElementById('parameter-fields-models').className = 'models-container show';
        document.getElementById('parameter-fields-submit').className = 'submit-container show';
    } else {
        document.querySelector('.slider-text').innerHTML = 'Parameter file';
        document.getElementById('parameter-file').className = 'form-container show';
        document.getElementById('parameter-file-models').className = 'models-container show';
        document.getElementById('parameter-file-submit').className = 'submit-container show';
    }
};

let displayFileName = function () {
    let str = this.parentElement.getAttribute('initial-text');
    if (this.files.length > 0) {
        let names = [];
        for (let i = 0; i < this.files.length; i++) {
            names.push(this.files[i].name);
        }
        str = names.join(' , ')
    }
    this.parentElement.setAttribute('data-text', str);
};

let msgboxPersistent = new MessageBox("#msgbox-area", {
    closeTime: 0,
    hideCloseButton: false
});

let msgboxTemporary = new MessageBox("#msgbox-area", {
    closeTime: 15 * 1000,
    hideCloseButton: false
});

let ganFormAlert = function () {
    msgboxPersistent.show("Please wait while the sample is generated.\nSynthetic data generation might take some time.");
    setTimeout(() => {
        msgboxPersistent.show("Generation ID was successfully created.\nYou can quit and come back later if you want.", 'success')
    }, 3 * 1000)
};

let init = function () {
    document.querySelectorAll('.selector').forEach((elem) => {
        elem.addEventListener('click', changeTab, false);
    });
    document.getElementById('form-switch').addEventListener('click', changeForm, false);
    document.querySelectorAll('.file-upload-field').forEach((elem) => {
        elem.addEventListener('change', displayFileName, false);
    });
    document.querySelectorAll('.file-upload-wrapper').forEach((elem) => {
        elem.setAttribute('data-text', elem.getAttribute('initial-text'));
    });
    document.querySelectorAll('.form').forEach((elem) => {
        elem.addEventListener('submit', ganFormAlert, false);
    });
};

documentReady(init);