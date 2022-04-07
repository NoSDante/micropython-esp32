function removeClassWildcard($element, removals) {
    if (removals.indexOf('*') === -1) {
        // Use native jQuery methods if there is no wildcard matching
        $element.removeClass(removals);
        return $element;
    }

    var patt = new RegExp('\\s' +
        removals.replace(/\*/g, '[A-Za-z0-9-_]+').split(' ').join('\\s|\\s') +
        '\\s', 'g');

    $element.each(function(i, it) {
        var cn = ' ' + it.className + ' ';
        while (patt.test(cn)) {
            cn = cn.replace(patt, ' ');
        }
        it.className = $.trim(cn);
    });

    return $element;
}

Element.prototype.removeClass = function(cls) {
    if (removals.indexOf('*') === -1) {
        // Use native jQuery methods if there is no wildcard matching
        this.classList.remove(cls);
        return this;
    }
    var patt = new RegExp('\\s' +
        cls.replace(/\*/g, '[A-Za-z0-9-_]+').split(' ').join('\\s|\\s') +
        '\\s', 'g');

    for (const [key, value] of Object.entries(this)) {
        var cn = ' ' + key.className + ' ';
        while (patt.test(cn)) {
            cn = cn.replace(patt, ' ');
        }
        item.className = cn.trim();
    }
    return this;
}

Element.prototype.disableItems = function() {
    this.querySelectorAll("input").setAttribute("disabled");
    this.querySelectorAll("button").setAttribute("disabled");
    this.querySelectorAll("select").setAttribute("disabled");
}

Element.prototype.enableItems = function() {
    this.querySelectorAll("input").removeAttribute("disabled");
    this.querySelectorAll("button").removeAttribute("disabled");
    this.querySelectorAll("select").removeAttribute("disabled");
}

function disableItems($element) {
    $element.find("input").attr("disabled", "disabled");
    $element.find("button").attr("disabled", "disabled");
    $element.find("select").attr("disabled", "disabled");
}

function enableItems($element) {
    $element.find("input").removeAttr("disabled");
    $element.find("button").removeAttr("disabled");
    $element.find("select").removeAttr("disabled");
}

const LOCAL = true;

/** MAIN */
var page = {

    init: function(config) {
        //$.extend(form.config, config);
        this.setup();
    },

    show: function(config) {
        //$.extend(page.config, config);
        $("#pageloading").remove();
        $(".wrapper").removeClass("visually-hidden");
    },

    message: function(msg, type = "info") {
        let cls = type;
        switch (type) {
            case "info":
                cls = "primary";
                break;
            case "error":
                cls = "danger";
                break;
        }
        let toast = document.getElementById('messagePage');
        document.getElementById('messageContent').innerHTML = msg;
        document.getElementById('messageType').innerHTML = type.charAt(0).toUpperCase() + type.slice(1);
        document.getElementById('messageTime').innerHTML = new Date().toLocaleTimeString('en-DE', { hour12: false });
        removeClassWildcard($(toast), "bg-*");
        toast.classList.add("bg-" + cls)
        new bootstrap.Toast(toast).show();
    },

    setup: function() {
        var sidebar = document.getElementById("sidebar");

        let tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
        tooltipTriggerList.map(function(tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl)
        })

        $(sidebar).mCustomScrollbar({
            theme: "minimal",
        });

        // observe window resize
        window.addEventListener('resize', function() {
            // get window width
            const iw = window.innerWidth;
            const bp = 768;
            // determine named size
            if (iw <= bp || iw > bp) {
                if (sidebar.classList.contains("active")) {
                    $("#sidebarCollapse").removeClass("active");
                } else {
                    $("#sidebarCollapse").addClass("active");

                }
                //console.log(iw);
            }
        });

        document.getElementById("sidebarCollapse").addEventListener("click", (event) => {
            event.target.classList.toggle("active");
            sidebar.classList.toggle("active");
            document.getElementById("content").classList.toggle("active");
        });

        $(".progress").each(function() {
            let value = $(this).attr("data-value");
            let left = $(this).find(".progress-left .progress-bar");
            let right = $(this).find(".progress-right .progress-bar");
            if (value > 0) {
                if (value <= 50) {
                    degree = (value / 100) * 360;
                    right.css("transform", "rotate(" + degree + "deg)");
                } else {
                    degree = ((value - 50) / 100) * 360;
                    right.css("transform", "rotate(180deg)");
                    left.css("transform", "rotate(" + degree + "deg)");
                }
            }
        });
    }

}

var server = {

    //url: "http://192.168.2.107:8080",
    url: "",
    base_url: "http://192.168.2.",
    base_start: 100,
    base_end: 113,
    name: "MicroWebSrv2",
    port: ":8080",
    connected: false,
    response: null,

    base: function(url = server.base_url) {

        page.init()

        let path = window.location.href.substring(0, (window.location.href.lastIndexOf("/")) + 1);
        $.getJSON(path + "server.json", function(obj) {
            $.each(obj, function(key, value) {
                server[key] = value;
            })
        });

        if (LOCAL == true) {
            let hit = false;
            for (let i = server.base_start = 100; i < server.base_end; i++) {
                url = server.base_url + i + server.port;
                if (server.hasOwnProperty("url") && server.url.length != 0) {
                    url = server.url
                }
                server.getLocal(url, function(callback) {
                    hit = true;
                    server.url = callback;
                    server.connected = true;
                    // init features
                    init();
                })
                if (hit == true) break;
            }
        } else {
            if (window.location.protocol == "http:") {
                console.log("url:", window.location.href)
                url = window.location.href.substring(0, (window.location.href.lastIndexOf("/")) + 1) + server.port;
                if (server.hasOwnProperty("url") && server.url.length != 0) {
                    url = server.url
                }
                server.get(url, function(callback) {
                    server.url = callback.substr(0, callback.length - 1);
                    server.connected = true;
                    // init features
                    init();
                })
            }
        }
    },

    get: function(url, callback) {
        $.ajax({
            url: url,
            type: "GET",
            timeout: 5000,
            async: true,
            success: function(data, textStatus, jqXHR) {
                // Get the raw header string
                var headers = jqXHR.getAllResponseHeaders();
                // Convert the header string into an array
                // of individual headers
                var arr = headers.trim().split(/[\r\n]+/);
                // Create a map of header names to values
                var headerMap = {};
                arr.forEach(function(line) {
                    var parts = line.split(': ');
                    var header = parts.shift();
                    var value = parts.join(': ');
                    headerMap[header] = value;
                });
                if (headerMap["server"].match(server.name)) {
                    console.log("HeaderMap: 'server' ", headerMap["server"])
                    page.message(headerMap["server"] + ' is connected', "info")
                    callback(url);
                }
            },
            complete: function(xhr, textStatus) {
                if (server.connected == false) {
                    let msg = document.getElementById("notConnected")
                    msg.classList.remove("visually-hidden");
                    msg.innerHTML = server.name + " is not connected!";
                } else {
                    let msg = document.getElementById("notConnected")
                    msg.classList.add("visually-hidden");
                }
            }
        })
    },

    getLocal: function(url, callback) {
        $.ajax({
            url: url + "/server",
            type: "GET",
            timeout: 10000,
            async: true,
            contentType: 'application/json; charset=utf-8',
            success: function(data, textStatus, jqXHR) {
                if (typeof(data) === undefined || data == null) {
                    console.log("getServerName no response")
                } else {
                    if (data.hasOwnProperty("server")) {
                        page.message(data["server"] + ' is connected', "info")
                        callback(url);
                    }
                }
            },
            complete: function(xhr, textStatus) {
                if (xhr.status == 200) {
                    // Get the raw header string
                    var headers = xhr.getAllResponseHeaders();
                    // Convert the header string into an array
                    // of individual headers
                    var arr = headers.trim().split(/[\r\n]+/);
                    // Create a map of header names to values
                    var headerMap = {};
                    arr.forEach(function(line) {
                        var parts = line.split(': ');
                        var header = parts.shift();
                        var value = parts.join(': ');
                        headerMap[header] = value;
                    });
                    if (headerMap["server"] !== undefined) {
                        if (headerMap["server"].match(server.name)) {
                            console.log("HeaderMap: 'server' ", headerMap["server"])
                            page.message(data["server"] + ' is connected', "info")
                            callback(url);
                        }
                    }
                };
                if (server.connected == false) {
                    let msg = document.getElementById("notConnected")
                    msg.classList.remove("visually-hidden");
                    msg.innerHTML = server.name + " is not connected!";
                } else {
                    let msg = document.getElementById("notConnected")
                    msg.classList.add("visually-hidden");
                }
            }
        })
    },

    ping: function(url) {
        $.ajax({
            url: url,
            type: 'GET',
            cache: false,
            dataType: 'json',
            complete: function() {
                console.log('ping ' + url);
            }
        });
    },

    sendRequest: function(url, data, callback) {
        let type = "POST";
        if (data === undefined) {
            type = 'GET';
        }
        $.ajax({
            url: url,
            type: type,
            data: data,
            cache: false,
            dataType: 'json',
            success: function(data, textStatus, jqXHR) {
                if (typeof(data) === undefined || data == null) {
                    page.message("Server error", "error")
                    console.log("no response")
                } else {
                    console.log(data)
                        // Callback
                    callback(data);
                    page.message(data["success"], "success")

                }
            },
            error: function(jqXHR, textStatus, errorThrown) {
                console.log("Exception " + jqXHR.responseText, errorThrown);
                page.message("Unknonw exception", "error")

            },
            complete: function() {
                console.log('sendRequest: complete');
            }
        });
    },

    getResponse: function() {
        return this.response;
    }

}

/** FEATURES */
var dashboard = {

    config: {
        dashboard: "#dashboard",
        resetItem: ".reset-item",
        resetButton: "#resetButton",
        setupItem: ".setup-item",
        setupButton: "#setupButton",
        rebootButton: "#rebootButton",
        wifiItem: ".wifi-item",
        wifiOnButton: "#wifiOnButton",
        wifiOffButton: "#wifiOffButton",
    },
    systemstate: {},

    init: function() {
        //$.extend(form.config, config);
        disableItems($(this.config.dashboard));
        this.setup();
        if (LOCAL == true) server.ping(server.url);
        this.getSystemState(function(callback) { dashboard.setSystemState(dashboard.systemstate = callback) });
    },

    setSystemState: function(callback) {
        let table = document.querySelector("#systemstateTable tbody");
        document.getElementById("systemstateTable").classList.remove("visually-hidden");
        document.getElementById("systemstateAlert").remove();
        for (const [key, value] of Object.entries(callback)) {
            table.insertRow(-1).innerHTML = '<tr><td>' + key + '</td><td>' + value + '</td></tr>';
        }
    },

    setupEvent: {

        setSystemItem: function(item, value) {}

    },


    // get systemstate
    getSystemState: function(callback) {
        $.ajax({
            url: server.url + "/systemstate",
            type: 'GET',
            cache: false,
            dataType: 'json',
            success: function(data, textStatus, jqXHR) {
                if (typeof(data) === undefined || data == null) {
                    console.log("getSystemState: no response")
                    page.message("Could not load systemstate", "error")
                } else {
                    if (data.hasOwnProperty("error")) {
                        page.message(data["error"], "error")
                    }
                    if (data.hasOwnProperty("info")) {
                        page.message(data["info"], "info")
                    }
                    if (data.hasOwnProperty("success")) {
                        page.message(data["success"], "info")
                        delete data["success"]
                        callback(data)
                        enableItems($(dashboard.config.dashboard));
                    }
                }
            },
            error: function(jqXHR, textStatus, errorThrown) {
                console.log("Exception " + jqXHR.responseText, errorThrown);
                page.message("Could not load systemstate", "error")
            },
            complete: function() {
                console.log('getSystemState: complete');
            }
        });
    },
    setup: function() {

        $("#dashboard .card").hover(
            function(event) {
                $(this).find("p.card-text").toggleClass("text-primary fw-bold");
                // Rainbow Border
                $(this).toggleClass("shadowcolorscheme");
                $(this).css("cursor", "pointer");
                //AP Item
                $(this).find(".fa-broadcast-tower").toggleClass("fa-fade");
                //Reset Item
                $(this).find(".fa-gear").toggleClass("fa-spin");
                //Reboot Item
                $(this).find(".fa-compact-disc").toggleClass("fa-spin");
                //WiFi Item
                $(this).find(".fa-wifi").toggleClass("fa-beat");
            });

        /** Items */
        // Reset
        $(this.config.resetItem).click(() => {
            var modal = new bootstrap.Modal(document.getElementById('resetModal'))
            modal.show();
        });
        // WiFi
        $(this.config.wifiItem).click(() => {
            var modal = new bootstrap.Modal(document.getElementById('wifiModal'))
            modal.show();
        });
        // Reboot
        $(this.config.setupItem).click(() => {
            var modal = new bootstrap.Modal(document.getElementById('rebootModal'))
            modal.show();
        });

        /** Actions */
        // Reset
        $(this.config.resetButton).click(() => {
            server.sendRequest(url = server.url + "/reset", data = undefined, function(callback) {
                if (callback.hasOwnProperty("success")) {
                    page.message(callback["success"], "success")
                    let info = document.getElementById("pageInfo");
                    info.classList.remove("visually-hidden")
                    info.innerHTML = callback["success"];
                    for (let i = 1; i < 100; i++) {
                        setTimeout(info.innerHTML = info.innerHTML + ".", 10);
                    }
                    window.location.reload();
                }
            })
        });
        // Setup
        $(this.config.setupButton).click(() => {
            server.sendRequest(url = server.url + "/resetbootfile", data = undefined, function(callback) {
                if (callback.hasOwnProperty("success")) {
                    page.message(callback["success"], "success")
                    let info = document.getElementById("pageInfo");
                    info.classList.remove("visually-hidden")
                    info.innerHTML = callback["success"];
                    for (let i = 1; i < 20; i++) {
                        setTimeout(function(callback) { callback = function() { info.innerHTML = info.innerHTML + "." } }, 1000);
                    }
                }
            })
        });
        // WiFi Off
        $(this.config.wifiOffButton).click(() => {
            server.sendRequest(url = server.url + "/wifiturnoff", data = undefined, function(callback) { server.response = callback })
        });
        // WiFi On
        $(this.config.wifiOnButton).click(() => {
            server.sendRequest(url = server.url + "/wifiturnon", data = undefined, function(callback) { server.response = callback })
        });
        // Setup + Reboot
        $(this.config.rebootButton).click(() => {
            server.sendRequest(url = server.url + "/resetbootfile", data = undefined, function(callback) {
                if (callback["success"]) {
                    if (LOCAL == true) server.ping(server.url);
                    setTimeout(server.sendRequest(url = server.url + "/reset", data = undefined, function(callback) { server.response = callback }), 1000);
                }
            })
        });
    },
}

var bootmgr = {

    config: {
        $loadBootConfig: $("#loadBootConfig"),
        $saveBootConfig: $("#saveBootConfig"),
        $bootmanager: $("#bootmanager")
    },

    objects: [
        "DEBUG",
        "NETWORK",
        "SDCARD",
        "I2C",
        "TIMEZONE",
        "RTC"
    ],

    data: {
        changed: false,
        delete: {},
        tmp: {},
        networks: {
            "default": {
                "essid": "",
                "password": "",
                "static_ip": false,
                "ip": "",
                "subnet": "",
                "gateway": "",
                "dns": ""
            }
        },
        boot: {},
        default: {
            "DEBUG": false,
            "TIMEZONE": {
                "UTC": 2,
                "ZONE": "MESZ - Mitteleuropäische Sommerzeit (UTC+2)",
            },
            "SDCARD": {
                "SPI": 1,
                "CS": 13,
                "MOSI": 2,
                "PATH": "/sd"
            },
            "RTC": {
                "MODUL": "DS1307"
            },
            "NETWORK": {
                "RECONNECT": 0,
                "WIFI": false,
                "SMART": false,
                "AP_IF": true,
                "AP": false
            },
            "I2C": {
                "SLOT": 1,
                "SDA": 21,
                "SCL": 22,
                "FREQ": 400000
            }
        }
    },

    init: function() {
        this.getBootConfig(function(callback) { bootmgr.data.boot = callback });
        this.network.init();
        this.sendEvent();
        this.loadEvent();
    },

    setup: function() {
        this.setupObjects(this.objects);
        this.network.setup();
        bootmgr.setupEvent.done = true;
    },

    // Click events save/load
    loadEvent: function() {
        this.config.$loadBootConfig.click(function() {
            bootmgr.getBootConfig(function(callback) { bootmgr.data.boot = callback });
        })
    },
    sendEvent: function() {
        this.config.$saveBootConfig.click(function() {
            bootmgr.saveBootConfig(function(callback) { bootmgr.data.boot = callback });
        })
    },

    // get data from server
    getBootConfig: function(callback) {
        disableItems(this.config.$bootmanager)
        $.ajax({
            url: server.url + "/bootconfig",
            type: 'GET',
            cache: false,
            dataType: 'json',
            success: function(data, textStatus, jqXHR) {
                if (typeof(data) === undefined || data == null) {
                    console.log("getBootConfig: no response")
                    page.message("Could not load bootconfig", "error")
                } else {
                    if (data.hasOwnProperty("error")) {
                        page.message(data["error"], "error")
                        console.log("getBootConfig:", data["error"])
                        bootmgr.data.boot = {};
                    }
                    if (data.hasOwnProperty("info")) {
                        //console.log("bootconfig data:", data)
                        page.message(data["info"] + "<br>Set default values", "info")
                            //delete bootmgr.data["info"]
                        callback(bootmgr.data.default);
                        enableItems(bootmgr.config.$bootmanager)
                        bootmgr.config.$saveBootConfig.attr("disabled", "disabled");
                        bootmgr.setup();
                    }
                    if (data.hasOwnProperty("success")) {
                        //console.log("bootconfig data:", data)
                        page.message(data["success"], "info")
                        delete bootmgr.data["success"]
                        callback(data);
                        enableItems(bootmgr.config.$bootmanager)
                        bootmgr.config.$saveBootConfig.attr("disabled", "disabled");
                        bootmgr.setup();
                    }
                }
            },
            error: function(jqXHR, textStatus, errorThrown) {
                console.log("Exception " + jqXHR.responseText, errorThrown);
                page.message("Could not load bootconfig", "error")
                bootmgr.data.boot = {};
                //bootmgr.data.boot = bootmgr.data.default;
            },
            complete: function() {
                console.log('getBootConfig: complete');

            }
        });
    },
    // save data on server
    saveBootConfig: function(callback) {
        // delete unused/not checked items
        bootmgr.deleteItems();
        $.ajax({
            url: server.url + "/savebootconfig",
            type: 'POST',
            contentType: 'application/json; charset=utf-8',
            data: JSON.stringify(bootmgr.data.boot),
            dataType: 'json',
            success: function(data, textStatus, jqXHR) {
                if (typeof(data) === undefined || data == null) {
                    page.message("Colud not save bootconfig!", "error")
                    console.log("saveBootConfig: no response")
                } else {
                    if (data.hasOwnProperty("error")) {
                        page.message(data["error"], "error")
                        console.log("saveBootConfig:", data["error"])
                    }
                    if (data.hasOwnProperty("success")) {
                        page.message(data["success"], "success")
                        delete bootmgr.data["success"]
                        callback(data);
                        bootmgr.setup();
                    }
                }
            },
            error: function(jqXHR, textStatus, errorThrown) {
                console.log("Exception " + jqXHR.responseText, errorThrown);
                page.message("Colud not save bootconfig!", "error")
            },
            complete: function() {
                console.log('saveBootConfig: complete');
            }
        });
    },

    // edit data object
    updateBootConfig: function(obj, key, value) {
        this.config.$saveBootConfig.removeAttr("disabled");
        this.data.changed = true;
        if (typeof(obj) !== undefined) {
            if (typeof(this.data.boot[obj]) === undefined) {
                this.data.boot[obj] = {};
            } else {
                if (value != null && key === undefined) {
                    this.data.boot[obj] = value;
                }
            }
            if (typeof(key) !== undefined) {
                this.data.boot[obj][key] = value;
            }
        }
    },
    deleteItems: function() {
        for (const [key] of Object.entries(bootmgr.data.delete)) {
            if (bootmgr.data.boot[key] !== undefined) {
                delete bootmgr.data.boot[key]
            }
        }
    },

    // markiert Labels, wenn Werte geändert wurden
    markCheckboxLabel: function($label, value) {
        if (value == true && $label.html() == "OFF" || value == false && $label.html() == "ON") {
            $label.addClass("text-dark").removeClass("text-white");
        }
        if (value == true && $label.html() == "ON" || value == false && $label.html() == "OFF") {
            $label.addClass("text-white").removeClass("text-dark");
        }
    },
    markInputLabel: function($label, value) {
        if (value == $label.html()) {
            $label.removeClass("fw-bold");
        } else {
            $label.addClass("fw-bold");
        }
    },

    // set Events
    setupEvent: {
        done: false,

        checkboxObject: function(obj, $element) {
            var $divObj = $("#edit" + obj.toUpperCase());
            var notDelete = ["DEBUG"];
            $element.click(
                function(event) {
                    let $checkbox = $(event.target);
                    let $label = $checkbox.parent().find(".object-label");
                    let key = $checkbox.attr("name");
                    let value = false;
                    if (key === undefined) return;
                    if ($checkbox.is(':checked')) {
                        value = true;
                    }
                    bootmgr.markCheckboxLabel($label, value)
                    if (value == false) {
                        disableItems($divObj)
                            // Check if a value not exists in the array
                        if (notDelete.indexOf(obj) === -1) {
                            bootmgr.data.delete[obj] = true;
                        } else {
                            bootmgr.updateBootConfig(obj, key = undefined, val = false);
                        }
                        bootmgr.config.$saveBootConfig.removeAttr("disabled");
                    }
                    if (value == true) {
                        enableItems($divObj);
                        // Check if a value not exists in the array
                        if (notDelete.indexOf(obj) === -1) {
                            delete bootmgr.data.delete[obj];
                        } else {
                            bootmgr.updateBootConfig(obj, key = undefined, val = true);
                        }
                    }

                }
            );
        },
        checkboxItem: function(obj, $element) {
            // Update Value & Switch Label
            $element.click(
                function(event) {
                    let $checkbox = $(event.target);
                    let $label = $checkbox.parent().parent().parent().find(".check-label");
                    let key = $checkbox.attr("name");
                    let value = false;
                    if (key === undefined) return;
                    if ($checkbox.is(':checked')) {
                        value = true;
                    }
                    bootmgr.markCheckboxLabel($label, value)
                    if (key == 'wifi' && value == true) {
                        bootmgr.updateBootConfig(obj, "reconnect".toUpperCase(), bootmgr.data.tmp["reconnect"]);
                        $("input[name=reconnect]").val(bootmgr.data.tmp["reconnect"]);
                        $("#Reconnect h5").html(bootmgr.data.tmp["reconnect"]);
                        $("#Reconnect button").removeAttr("disabled");
                        $("input[name=reconnect]").removeAttr('disabled');
                    }
                    if (key == 'wifi' && value != true) {
                        bootmgr.updateBootConfig(obj, "reconnect".toUpperCase(), 0);
                        $("#Reconnect button").attr('disabled', 'disabled');
                        $("input[name=reconnect]").attr('disabled', 'disabled');
                        $("input[name=reconnect]").val(0);
                        $("#Reconnect h5").html("0")
                    }
                    bootmgr.updateBootConfig(obj, key.toUpperCase(), value);
                }
            );
        },
        inputItem: function(obj, $element) {
            $element.blur(
                function() {
                    let $input = $(this);
                    let key = $input.attr("name");
                    let value = $input.val();
                    let $label = $input.parent().parent().parent().find(".text-label");
                    if (key === undefined) {
                        return;
                    }
                    bootmgr.updateBootConfig(obj, key.toUpperCase(), value);
                    bootmgr.markInputLabel($label, value);
                }
            );
        },
        selectItem: function(obj, $element) {
            $element.change(
                function() {
                    let $select = $(this);
                    let key = $select.attr("name");
                    let value = $select.val();
                    let $label = $select.parent().parent().find(".text-label");
                    if (key === undefined) {
                        return;
                    }
                    bootmgr.updateBootConfig(obj, key.toUpperCase(), value);
                    bootmgr.markInputLabel($label, value);

                }
            );
        }
    },

    // set events / data values
    setupObjects: function(objects) {
        objects.forEach(function(item) {
            let $editObj = $("input[name=" + item.toLowerCase() + "]");
            let $label = $editObj.parent().find(".check-label.badge");
            if (bootmgr.data.boot.hasOwnProperty(item)) {
                $editObj.attr("checked", "checked");
                bootmgr.setCheckbox($editObj, true);
                bootmgr.setLabel($label, true);
                if (bootmgr.setupEvent.done == false) {
                    bootmgr.setupEvent.checkboxObject(item, $editObj);
                }
                for (const [key, value] of Object.entries(bootmgr.data.boot[item])) {
                    bootmgr.setupItems(key, value, item)
                }
            } else if (!$editObj.is(":checked")) {
                enableItems($("#edit" + item.toUpperCase()));
            }
        });
    },
    setupItems: function(key, value, obj) {
        let $element = $("[name=" + key.toLowerCase() + "]");
        if ($element !== undefined) {
            // Checkbox + Label
            if (typeof(value) === 'boolean' && $element.prop("type") == "checkbox") {
                let $label = $element.parent().parent().parent().find(".check-label");
                if (value == true) {
                    $element.attr("checked", "");
                    $label.removeClass("text-dark").addClass("text-white");
                    $label.removeClass("bg-danger").addClass("bg-success");
                    $label.html("ON");
                } else {
                    $element.removeAttr("checked");
                    $label.removeClass("text-dark").addClass("text-white");
                    $label.removeClass("bg-success").addClass("bg-danger");
                    $label.html("OFF");
                }
                if (bootmgr.setupEvent.done == false) {
                    bootmgr.setupEvent.checkboxItem(obj, $element);
                }
                bootmgr.markCheckboxLabel($label, value);
            }
            // Input, Select + Label
            if (typeof(value) === "string" || typeof(value) === "number") {
                if ($element.is("input")) {
                    let $label = $element.parent().parent().parent().find(".text-label");
                    $element.val(value);
                    $label.html(value);
                    if (bootmgr.setupEvent.done == false) {
                        bootmgr.setupEvent.inputItem(obj, $element);
                    }
                    bootmgr.markInputLabel($label, value);
                }
                if ($element.is("select")) {
                    let $label = $element.parent().parent().find(".text-label");
                    $element.find("option[value=" + value + "]").attr("selected", "select");
                    $label.html(value);
                    if (bootmgr.setupEvent.done == false) {
                        bootmgr.setupEvent.selectItem(obj, $element);
                    }
                    bootmgr.markInputLabel($label, value);
                }
            }
        }
    },
    setLabel: function($lb, value) {
        if (value == true) {
            $lb.removeClass("text-dark").addClass("text-white");
            $lb.removeClass("bg-danger").addClass("bg-success");
            $lb.html("ON");
        }
        if (value == false) {
            $lb.removeClass("text-dark").addClass("text-white");
            $lb.removeClass("bg-success").addClass("bg-danger");
            $lb.html("OFF");
        }
    },
    setCheckbox: function($cb, value) {
        if (value == true) $cb.attr("checked", "checked");
        if (value == false) $cb.removeAttr("checked");
    },

    network: {

        setup: function() {
            let $editReconnect = $("#Reconnect button");
            let $inputReconnect = $("input[name=reconnect]");
            if (bootmgr.data.boot.hasOwnProperty("NETWORK")) {
                if (bootmgr.data.boot["NETWORK"].hasOwnProperty("WIFI")) {
                    let value = bootmgr.data.boot["NETWORK"]["WIFI"];
                    if (value == false) {
                        $editReconnect.attr('disabled', 'disabled');
                        $inputReconnect.attr('disabled', 'disabled');
                    }
                    if (value == true) {
                        $editReconnect.removeAttr('disabled');
                        $inputReconnect.removeAttr('disabled');
                    }
                }
                bootmgr.data.tmp["default"] = $("input[name=default]").val();
                bootmgr.data.tmp["reconnect"] = $("input[name=reconnect]").val();
            } else {
                bootmgr.data.tmp["reconnect"] = 0;
            }
        },

        init: function() {

            // Click => edit reconnect
            $("#Reconnect button").click(
                function() {
                    var $input = $("input[name=reconnect]");
                    var $label = $("#Reconnect h5");
                    $label.toggleClass("visually-hidden");
                    $input.toggleClass("visually-hidden");
                    if (!$input.hasClass("visually-hidden")) {
                        $input.removeAttr("disabled")
                        $input.focus()
                    }
                    $label.html($input.val());
                }
            );

            // Blur => validate reconnect value
            $("input[name=reconnect]").blur(
                function() {
                    let $input = $(this);
                    let key = $input.attr("name");
                    let value = $input.val();
                    if (value == "") {
                        $input.val(0);
                        value = 0;
                    }
                    if (key === undefined) {
                        return;
                    }
                    bootmgr.data.tmp["reconnect"] = value;
                }
            );

            // Blur => set value 0 if 'smart' is not checked
            $("input[name=default]").blur(
                function() {
                    let $input = $(this);
                    let value = $input.val();
                    if (value == "" && !$("input[name=smart]").is(':checked')) {
                        $input.val(bootmgr.data.tmp["default"]);
                    } else {
                        bootmgr.data.tmp["default"] = value;
                    }
                }
            );

            // Click => set selected default network from list
            $("#selectDefaultNetwork").find("li a").click(
                function() {
                    let $input = $("input[name=default]");
                    let value = $(this).html();
                    $input.val(value);
                    bootmgr.data.tmp["default"] = value;
                    $input.trigger("blur");
                }
            );
        }
    },

    networks: {
        init: function() {},
        setup: function() {}
    }
}

var sensor = {

    init: function() {
        this.getSensorData();
        this.setup()
    },

    setup: function() {
        let getSensorData = document.getElementById("getSensorData")

        getSensorData.addEventListener("click", (event) => {
            sensor.getSensorData();

        });
    },

    getSensorData: function() {
        var eventSource;

        if (!!window.EventSource) {
            eventSource = new EventSource(server.url + "/sensordata");

        } else {
            page.message('Dein Browser untestützt keine HTML5 Server-Sent Events', 'error');
            return;
        }

        eventSource.addEventListener('open', () => {
            console.log('Verbindung wurde erfolgreich hergestellt.');
        });

        eventSource.addEventListener('message', (event) => {
            if (typeof(event.data) === undefined || event.data == null) {
                console.log("getSensorData: no response")
            } else {
                let data = JSON.parse(event.data);
                if (data.hasOwnProperty("error")) {
                    page.message(data["error"], "error")
                }
                if (data.hasOwnProperty("info")) {
                    page.message(data["info"] + "info")
                }
                if (data.hasOwnProperty("success")) {
                    console.log('getSensorData:', event.data);
                    page.message(data["success"], "info")
                }
            }
            console.log('getSensorData:', event.data);
        });

        eventSource.addEventListener('error', (event) => {
            console.log("error:", event);
            eventSource.close();
            page.message('EventSource "getSensorData" connection closed.', 'error');
        });

    },

    setSensorData: function() {}
}