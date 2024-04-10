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

function timeout(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

const LOCAL = true;

/** MAIN */
var page = {

    init: function() {
        this.setup();
        this.show();
    },

    show: function(config) {
        //$.extend(page.config, config);
        $("#pageloading").remove();
        $(".wrapper").removeClass("visually-hidden");
    },

    // page message
    message: function(msg, type = "info") {
        let cls = type;
        switch (type) {
            case "info":
                cls = "primary";
                break;
            case "error":
                cls = "danger";
                break;
            case "warning":
                cls = "warning";
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

        // sidebar scrollbar
        let sidebar = document.getElementById("sidebar");
        $(sidebar).mCustomScrollbar({
            theme: "minimal",
        });

        // tooltips
        let tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
        tooltipTriggerList.map(function(tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl)
        })

        // TODO
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

        // sidebar navigation
        document.getElementById("sidebarCollapse").addEventListener("click", (event) => {
            event.target.classList.toggle("active");
            sidebar.classList.toggle("active");
            document.getElementById("content").classList.toggle("active");
        });

    }

}

var server = {

    ap_url: "http://192.168.1.4:8080",
    url: "",
    base_url: "http://192.168.2.",
    base_start: 100,
    base_end: 116,
    name: "MicroWebSrv2",
    port: ":8080",
    connected: false,
    ap: false,

    base: function(url = server.base_url) {

        // server settings from json-file
        let path = window.location.href.substring(0, (window.location.href.lastIndexOf("/")) + 1);
        $.getJSON(path + "server.json", function(obj) {
            $.each(obj, function(key, value) {
                server[key] = value;
            })
        });

        // local must find server-ip
        if (LOCAL == true) {
            let hit = false;
            for (let i = server.base_start = 100; i <= server.base_end; i++) {
                url = server.base_url + i + server.port;
                if (server.hasOwnProperty("url") && server.url.length != 0) {
                    url = server.url
                }
                console.log(url, " connecting...")
                server.getLocal(url, function(callback) {
                    hit = true;
                    server.url = callback;
                    server.connected = true;
                    console.log("server url:", server.url)
                        // init features
                    init();
                })
                if (hit == true) break;
            }
            // let counter = server.base_start;
            // for (let i = server.base_start = 100; i <= server.base_end; i++) {
            //     let url = server.base_url + i + server.port;
            //     let msg = document.getElementById("notConnected")
            //     server.getLocal(url, function(callback) {
            //         counter++;
            //         if (counter == server.base_end) {
            //             switch (server.url.length) {
            //                 case 0:
            //                     msg.classList.remove("visually-hidden");
            //                     msg.innerHTML = server.name + " is not connected!";
            //                     break;
            //                 case 1:
            //                     msg.classList.add("visually-hidden");
            //                     server.url = callback;
            //                     server.connected = true;
            //                     // init features
            //                     init();
            //                     break;
            //             }
            //             if (server.url.length > 1) {
            //                 // msg.classList.add("visually-hidden");
            //                 // server.url = callback;
            //                 // server.connected = true;
            //                 // init features
            //                 // init();
            //                 let list = document.getElementById("listServer")
            //                 let ul = document.createElement('ul');
            //                 list.innerHTML = server.url.length + " " + server.name + " found!";
            //                 list.appendChild(ul);
            //                 list.classList.remove("visually-hidden");
            //                 server.url.forEach(function(item, index, array) {
            //                     let li = document.createElement('li');
            //                     ul.appendChild(li);
            //                     li.innerHTML += "<a target=_blank href=" + item + ">" + server.name + " (" + item + ")</a>";
            //                 });
            //             }
            //         }
            //     })
            // }
        } else {
            if (window.location.protocol == "http:") {
                if (server.hasOwnProperty("url") && server.url.length != 0) {
                    url = server.url
                } else {
                    url = window.location.href.substring(0, window.location.href.lastIndexOf("/"));
                }
                console.log(url, " connecting...")
                server.get(url, function(callback) {
                    server.url = callback;
                    server.connected = true;
                    console.log("server url:", server.url)
                        // init features
                    init();
                })
            }
        }
    },

    // access point
    ap: function(url = server.ap_url) {
        console.log(url, " connecting...")
        server.getLocal(url, function(callback) {
            hit = true;
            server.url = callback;
            server.connected = true;
            server.ap = true;
            console.log("server url:", server.url)
                // init features
            init();
        })
    },

    // get server-name from header
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

    // get server-name from response
    getLocal: function(url, callback) {
        $.ajax({
            url: url + "/server",
            type: "GET",
            timeout: 5000,
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
            success: function() {
                console.log('success ping ' + url);
            },
            error: function() {
                console.log('error ping ' + url);
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
        wifiState: ".wifiState",
        apItem: ".ap-item",
        apOnButton: "#apOnButton",
        apOffButton: "#apOffButton",
        apState: ".apState"
    },

    systemstate: {},

    init: function() {
        //$.extend(form.config, config);
        disableItems($(this.config.dashboard));
        this.setupEvent.done = false;
        this.setup();
        if (LOCAL == true) server.ping(server.url);
        this.getSystemState(function(callback) { dashboard.setSystemState(dashboard.systemstate = callback) });
    },

    setApState: function(state, cls) {
        let item = document.querySelector(dashboard.config.apState);
        removeClassWildcard($(item), "text-*")
        item.classList.add(cls);
        item.innerHTML = state;
        let icon = document.querySelector(".faAp");
        removeClassWildcard($(icon), "text-*")
        icon.classList.remove("text-danger");
        icon.classList.remove("text-success");
        icon.classList.add(cls);
    },

    setWifiState: function(state, cls) {
        let item = document.querySelector(dashboard.config.wifiState);
        removeClassWildcard($(item), "text-*")
        item.classList.add(cls);
        item.innerHTML = state;
        let icon = document.querySelector(".faWifi");
        removeClassWildcard($(icon), "text-*")
        icon.classList.add(cls);
    },

    setNetState: function(callback) {
        for (const [key, value] of Object.entries(callback)) {
            let state = "unknown";
            let item = [];
            let cls = "text-dark";

            if (key == "WIFI") {
                if (value == "true") {
                    state = "On";
                    if (callback["CONNECTED"] == "true") {
                        state = "Verbunden";
                        cls = "text-success";
                    } else {
                        state = "keine Verbindung";
                        cls = "text-danger";
                    }
                } else {
                    state = "Off";
                }
                this.setWifiState(state, cls);
            };

            cls = "text-dark";
            state = "unknown";
            if (key == "AP" || key == "AP_IF") {
                if (callback["AP_IP_ADDRESS"] != "0.0.0.0") {
                    state = "Aktiv";
                    cls = "text-success"
                } else {
                    state = "Inaktiv";
                    cls = "text-danger"
                }
                this.setApState(state, cls);

            };

        }
    },

    setSystemState: function(callback) {
        this.showSystemState(callback);
        this.setNetState(callback);
    },

    showSystemState: function(callback) {
        let table = document.querySelector("#systemstateTable tbody");
        document.getElementById("systemstateTable").classList.remove("visually-hidden");
        document.getElementById("systemstateAlert").remove();
        for (const [key, value] of Object.entries(callback)) {
            table.insertRow(-1).innerHTML = '<tr><td>' + key + '</td><td>' + value + '</td></tr>';

        }
    },

    setup: function() {
        if (this.setupEvent.done == false) {
            this.setupEvent();
        }
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

    setupEvent: function() {

        $("#dashboard .card").hover(
            function(event) {
                $(this).find("p.card-text").toggleClass("text-primary fw-bold");
                // Rainbow Border
                $(this).toggleClass("shadowcolorscheme");
                $(this).css("cursor", "pointer");
                //AP Item
                $(this).find(".faAp").toggleClass("fa-fade");
                //Reset Item
                $(this).find(".fa-gear").toggleClass("fa-spin");
                //Reboot Item
                $(this).find(".fa-compact-disc").toggleClass("fa-spin");
                //WiFi Item
                $(this).find(".fa-wifi").toggleClass("fa-beat");
            }
        );

        // Reset-Item
        $(this.config.resetItem).click(() => {
            var modal = new bootstrap.Modal(document.getElementById('resetModal'))
            modal.show();
        });
        // Setup-Item
        $(this.config.setupItem).click(() => {
            var modal = new bootstrap.Modal(document.getElementById('rebootModal'))
            modal.show();
        });
        // WiFi-Item
        $(this.config.wifiItem).click(() => {
            var modal = new bootstrap.Modal(document.getElementById('wifiModal'))
            modal.show();
        });
        // Ap-Item
        $(this.config.apItem).click(() => {
            var modal = new bootstrap.Modal(document.getElementById('apModal'))
            modal.show();
        });

        // Reset (ESP32: machine.reset())
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
        // Setup (ESP32: delete boot.db)
        $(this.config.setupButton).click(() => {
            server.sendRequest(url = server.url + "/resetbootfile", data = undefined, function(callback) {
                if (callback.hasOwnProperty("success")) {
                    page.message(callback["success"], "success")
                }
                if (callback.hasOwnProperty("error")) {
                    page.message(callback["success"], "success")
                }
            })
        });
        // WiFi Off
        $(this.config.wifiOffButton).click(() => {
            server.sendRequest(url = server.url + "/wifiturnoff", data = undefined, function(callback) {
                if (callback.hasOwnProperty("success")) {
                    page.message(callback["success"], "success")
                    dashboard.setWifiState("Off", "text-danger")
                }
                if (callback.hasOwnProperty("error")) {
                    page.message(callback["error"], "error")
                }
            })

        });
        // WiFi On
        $(this.config.wifiOnButton).click(() => {
            server.sendRequest(url = server.url + "/wifiturnon", data = undefined, function(callback) {
                if (callback.hasOwnProperty("success")) {
                    page.message(callback["success"], "success")
                    dashboard.setWifiState("On", "text-success")
                }
                if (callback.hasOwnProperty("error")) {
                    page.message(callback["error"], "error")
                }
            })

        });
        // Ap On
        $(this.config.apOnButton).click(() => {
            server.sendRequest(url = server.url + "/apturnon", data = undefined, function(callback) {
                if (callback.hasOwnProperty("success")) {
                    page.message(callback["success"], "success")
                    dashboard.setApState("Aktiv", "text-success")
                }
                if (callback.hasOwnProperty("error")) {
                    page.message(callback["error"], "error")
                }
            })
        });
        // Ap Off
        $(this.config.apOffButton).click(() => {
            server.sendRequest(url = server.url + "/apturnoff", data = undefined, function(callback) {
                if (callback.hasOwnProperty("success")) {
                    page.message(callback["success"], "success")
                    dashboard.setApState("Inaktiv", "text-danger")
                }
                if (callback.hasOwnProperty("error")) {
                    page.message(callback["error"], "error")
                }
            })
        });
        // Setup/Reset
        $(this.config.rebootButton).click(() => {
            server.sendRequest(url = server.url + "/resetbootfile", data = undefined, function(callback) {
                if (callback["success"]) {
                    if (LOCAL == true) server.ping(server.url);
                    setTimeout(server.sendRequest(url = server.url + "/reset", data = undefined, function(callback) { server.response = callback }), 1000);
                }
            })
        });

        done = true;
    },
}

var bootmgr = {

    config: {
        $loadBootConfig: $("#loadBootConfig"),
        $saveBootConfig: $("#saveBootConfig"),
        $saveAndBoot: $("#saveAndBoot"),
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
                "MISO": 2,
                "WIDTH": 1,
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
                "AP": false,
                "DEFAULT": ""
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
        this.networks.getNetworks(function(callback) { bootmgr.network.setNetworks(callback) });
        this.network.init();
        this.sendEvent();
        this.loadEvent();
        this.restartEvent();
    },

    setup: function() {
        this.setupObjects(this.objects);
        this.network.setup();
        this.data.delete = {};
        this.setupEvent.done = true;
    },

    // Click events load/send/restart
    loadEvent: function() {
        this.config.$loadBootConfig.click(function() {
            bootmgr.getBootConfig(function(callback) { bootmgr.data.boot = callback });
            bootmgr.networks.getNetworks(function(callback) { bootmgr.network.setNetworks(callback) });
        })
    },
    sendEvent: function() {
        bootmgr.config.$saveBootConfig.click(function() {
            bootmgr.saveBootConfig(function(callback) { bootmgr.data.boot = callback });
        })
    },
    // Restart
    restartEvent: function() {
        bootmgr.config.$saveAndBoot.click(function() {
            bootmgr.saveBootConfig(function(callback) {
                bootmgr.data.boot = callback;
                if (LOCAL == true) server.ping(server.url);
                server.sendRequest(url = server.url + "/resetbootfile", data = undefined, function(callback) {
                    if (callback["success"]) {
                        if (LOCAL == true) server.ping(server.url);
                        server.sendRequest(url = server.url + "/reset", data = undefined, function(callback) { server.response = callback });
                    }
                })
            });

        });
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
                }
                if (data.hasOwnProperty("error")) {
                    page.message(data["error"], "error")
                    console.log("getBootConfig:", data["error"])
                    bootmgr.data.boot = {};
                }
                if (data.hasOwnProperty("info")) {
                    //console.log("bootconfig data:", data)
                    page.message(data["info"] + "<br>Set default values", "info")
                        //delete data["info"]
                    callback(bootmgr.data.default);
                    enableItems(bootmgr.config.$bootmanager)
                    bootmgr.config.$saveBootConfig.attr("disabled", "disabled");
                    bootmgr.setup();
                }
                if (data.hasOwnProperty("success")) {
                    //console.log("bootconfig data:", data)
                    page.message(data["success"], "info")
                    delete data["success"];
                    callback(data);
                    enableItems(bootmgr.config.$bootmanager)
                    bootmgr.config.$saveBootConfig.attr("disabled", "disabled");
                    bootmgr.setup();
                }
            },
            error: function(jqXHR, textStatus, errorThrown) {
                console.log("Exception " + jqXHR.responseText, errorThrown);
                page.message("Could not load bootconfig", "error")
                bootmgr.data.boot = {};
            },
            complete: function() {
                bootmgr.config.$loadBootConfig.removeAttr("disabled");
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
                    return;
                }
                if (data.hasOwnProperty("error")) {
                    page.message(data["error"], "error")
                    console.log("saveBootConfig:", data["error"])
                }
                if (data.hasOwnProperty("success")) {
                    page.message(data["success"], "success")
                    delete data["success"]
                    callback(data);
                    bootmgr.setup();
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
        for (const [key] of Object.entries(this.data.delete)) {
            if (this.data.boot[key] !== undefined) {
                delete this.data.boot[key]
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
                    let key = $checkbox.attr("name");
                    if (key === undefined) return;
                    let $label = $checkbox.parent().find(".object-label");
                    let value = false;
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
                        if (!bootmgr.data.boot.hasOwnProperty(obj)) {
                            obj = key.toUpperCase()
                            bootmgr.data.boot[obj] = Object.assign({}, bootmgr.data.default[obj]);
                            bootmgr.setupEvent.done = false;
                            for (const [key, value] of Object.entries(bootmgr.data.boot[obj])) {
                                bootmgr.setupItems(key, value, obj)
                            }
                            bootmgr.setupEvent.done = true;
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
                    if (typeof value === "string") {
                        if (!isNaN(parseInt(value))) {
                            value = parseInt(value);
                        }
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
                    let $option = $select.find("option:selected");

                    if ($option.attr("key") == "zone") {
                        if ($option.attr("data")) {
                            bootmgr.updateBootConfig(obj, $option.attr("key").toUpperCase(), $option.attr("data"));
                        } else {
                            bootmgr.updateBootConfig(obj, $option.attr("key").toUpperCase(), "(UTC+" + value + ")");
                        }
                        //bootmgr.updateBootConfig(obj, key.toUpperCase(), value);
                        //bootmgr.markInputLabel($label, value);
                        //return;
                    }
                    if (typeof value === "string") {
                        if (!isNaN(parseInt(value))) {
                            value = parseInt(value);
                        }
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
                for (const [key, value] of Object.entries(bootmgr.data.boot[item])) {
                    bootmgr.setupItems(key, value, item)
                }

                if (item == "DEBUG" && bootmgr.data.boot["DEBUG"] == false) {
                    $editObj.removeAttr("checked");
                    bootmgr.setCheckbox($editObj, false);
                    bootmgr.setLabel($label, false);
                }
            } else {
                disableItems($("#edit" + item.toUpperCase()));
                $editObj.removeAttr("checked");
                bootmgr.setCheckbox($editObj, false);
                bootmgr.setLabel($label, false);
            }
            if (bootmgr.setupEvent.done == false) {
                bootmgr.setupEvent.checkboxObject(item, $editObj);
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
        },

        setNetworks: function(networks) {
            let list = document.getElementById("selectDefaultNetwork");
            list.innerHTML = "";
            let input = document.querySelector("input[name=default]");
            Object.entries(networks).forEach(([key, value]) => {
                let li = document.createElement('li');
                let a = document.createElement('a');
                a.classList.add("dropdown-item");
                a.innerHTML = value;
                list.appendChild(li);
                li.appendChild(a);
                a.addEventListener("click", (event) => {
                    input.value = value;
                    input.focus();
                });
                if (bootmgr.data.boot.hasOwnProperty("NETWORK") && value == bootmgr.data.boot.NETWORK.DEFAULT) {
                    input.value = value;
                    a.classList.add("text-primary");
                }
            })
        }
    },

    networks: {
        init: function() {},
        setup: function() {},

        // get data from server
        getNetworks: function(callback) {
            $.ajax({
                url: server.url + "/networks",
                type: 'GET',
                cache: false,
                dataType: 'json',
                success: function(data, textStatus, jqXHR) {
                    if (typeof(data) === undefined || data == null) {
                        console.log("getNetworks: no response")
                        page.message("Could not load networks", "error")
                    } else {
                        if (data.hasOwnProperty("error")) {
                            page.message(data["error"], "error")
                            console.log("getNetworks:", data["error"])
                            bootmgr.data.networks = {};
                        }
                        if (data.hasOwnProperty("info")) {
                            //console.log("networks:", data)
                            page.message(data["info"], "info")
                            bootmgr.data.networks = {};
                        }
                        if (data.hasOwnProperty("success")) {
                            //console.log("networks:", data)
                            // page.message(data["success"], "info")
                            delete data["success"];
                            callback(data);
                        }
                    }
                },
                error: function(jqXHR, errorThrown) {
                    console.log("getNetworks: ", errorThrown);
                    page.message("Could not load networks", "error")
                    bootmgr.data.networks = {};
                },
                complete: function() {
                    console.log('getNetworks: complete');

                }
            });
        }
    }
}

var sensor = {

    running: false,
    retrys: 2,
    data_error: false,
    timeout: 7000,
    loadSensors: document.getElementById("loadSensors"),
    startSensorDataStream: document.getElementById("startSensorDataStream"),
    startSensorData: document.getElementById("startSensorData"),
    stopSensorData: document.getElementById("stopSensorData"),
    loadingSpinner: document.body.querySelector(".lds"),
    state: document.body.querySelector(".state"),

    init: function() {
        this.getSensors(function(callback) {
            this.sensors = callback;
            if (this.sensors.length == 0) {
                return;
            }
            sensor.loadSensors.classList.add("visually-hidden");
            Object.entries(this.sensors).forEach(([sname, state]) => {
                if (state == true) {
                    // console.log("active sensor", sname);
                    if (sname == "scd30") {
                        document.getElementById(sname).classList.remove("visually-hidden");
                        sensor.start(sname);
                        sensor.setup(sname);
                    }
                }
                //console.log(sname, state);
            })
        });
        // this.start();
        // this.setup();
    },


    setup: function(snam) {
        let obj = document.getElementById(snam);
        if (obj != null) {
            let startSensorData = obj.querySelector(".startSensorData");
            let stopSensorData = obj.querySelector(".stopSensorData");
            let startSensorDataStream = obj.querySelector(".startSensorDataStream");
            startSensorData.addEventListener("click", () => { this.start(snam); });
            stopSensorData.addEventListener("click", () => { this.stop(snam); });
            //
            // startSensorDataStream.addEventListener("click", () => { this.startStream(snam); });
        }

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
    },

    startStream: function(sname) {
        sensor.getSensorDataStream(sname);
    },

    // start: function(sname) {
    //     this.id = 1;
    //     this.name = sname
    //     this.running = true;
    //     this.data_error = 0;
    //     this.async = false;
    //     this.getSensorData(sname, function() { sleep(10000) });
    //     // nextSensorData(sensor.timeout)
    //     this.startSensorData.classList.add("visually-hidden");
    //     this.stopSensorData.classList.remove("visually-hidden");
    //     this.loadingSpinner.classList.add("lds-hourglass");
    //     removeClassWildcard($(this.state), "text-*");
    //     this.state.innerHTML = "RUNNING";
    //     this.state.classList.add("text-success");
    //     console.log('getSensordata: started');
    // },

    start: async function(modul) {
        this.modul = new Object();
        this.modul.id = 0;
        this.modul.name = modul
        this.modul.running = true;
        this.modul.error = 0;
        this.modul.async = true;
        this.modul.interval = 6000;

        this.startSensorData.classList.add("visually-hidden");
        this.stopSensorData.classList.remove("visually-hidden");
        this.loadingSpinner.classList.add("lds-hourglass");
        removeClassWildcard($(this.state), "text-*");
        this.state.innerHTML = "RUNNING";
        this.state.classList.add("text-success");

        console.log('getSensordata: started', modul);

        while (this.modul.running == true && this.modul.error < sensor.retrys) {
            this.modul.id++;
            if (this.modul.error != 0) {
                console.log('getSensordata: retry ', this.modul.error);
                // sensor.restart(sname);
            }
            if (this.modul.id == sensor.retrys && this.modul.error == 0) this.modul.async = true;
            if (this.modul.running == true && this.modul.error > sensor.retrys) {
                page.message("Could not load sensordata " + this.modul.name, "error")
                this.error(modul);
                this.stop(modul);
            }
            this.getSensorData(modul);
            await timeout(this.modul.interval);
        }
    },

    _start: async function(sname) {
        this.id = 0;
        this.name = sname
        this.running = true;
        this.data_error = 0;
        this.async = true;
        this.timeout = 6000;
        this.startSensorData.classList.add("visually-hidden");
        this.stopSensorData.classList.remove("visually-hidden");
        this.loadingSpinner.classList.add("lds-hourglass");
        removeClassWildcard($(this.state), "text-*");
        this.state.innerHTML = "RUNNING";
        this.state.classList.add("text-success");
        console.log('getSensordata: started');
        while (this.running == true && this.data_error < sensor.retrys) {
            sensor.id++;
            if (sensor.data_error != 0) {
                console.log('getSensordata: retry ', sensor.data_error);
                // sensor.restart(sname);
            }
            if (this.id == sensor.retrys && this.data_error == 0) this.async = true;
            if (this.running == true && this.data_error > sensor.retrys) {
                page.message("Could not load sensordata", "error")
                sensor.error();
                sensor.stop(sname);
            }
            sensor.getSensorData(sname);
            await timeout(sensor.timeout);
            // sleep(sensor.timeout);
        }
    },

    stop: function(modul) {
        this.modul.running = false;
        this.stopSensorData.classList.add("visually-hidden");
        this.startSensorData.classList.remove("visually-hidden");
        this.loadingSpinner.classList.remove("lds-hourglass");
        removeClassWildcard($(this.state), "text-*");
        this.state.innerHTML = "STOPPED";
        this.state.classList.add("text-warning");
        console.log('getSensordata: stopped');
    },

    restart: async function(modul) {
        this[modul].running = false;
        this[modul].error = 0;
        await timeout(this[modul].timeout);
        this[modul].running = true;
    },

    // restart: function(snam) {
    //     this.running = false;
    //     sleep(sensor.timeout)
    //     this.running = true;
    //     sleep(2000)
    //     this.getSensorData(snam);
    // },

    error: function(msg = "ERROR") {
        removeClassWildcard($(this.state), "text-*");
        this.state.innerHTML = msg;
        this.state.classList.add("text-danger");
    },

    info: function(msg = "No Snesor Data") {
        removeClassWildcard($(this.state), "text-*");
        this.state.innerHTML = msg;
        this.state.classList.add("text-warning");
    },

    // get used sensors from esp
    getSensors: function(callback) {
        $.ajax({
            url: server.url + "/sensors",
            type: 'GET',
            cache: false,
            async: true,
            dataType: 'json',
            success: function(data) {
                if (typeof(data) === undefined || data == null) {
                    console.log("getSensors: no response")
                    page.message("Could not load sensors", "error")
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
                    }
                }
            },
            error: function(jqXHR, textStatus, errorThrown) {
                console.log("getSensors: " + errorThrown);
                page.message("Could not load sensors", "error")
            },
            complete: function() {
                console.log('getSensors: complete');
            }
        });
    },

    // get sensor data
    getSensorDataStream: function(sname) {

        var eventSource;

        if (!!window.EventSource) {
            eventSource = new EventSource(server.url + "/sensordatastream");

        } else {
            page.message('Dein Browser untestützt keine HTML5 Server-Sent Events', 'error');
            return;
        }

        eventSource.addEventListener('open', () => {
            console.log('Verbindung wurde erfolgreich hergestellt.');
        });

        eventSource.addEventListener('message', (event) => {
            if (typeof(event.data) === undefined || event.data == null) {
                console.log("getSensorDataStream: no response")
            } else {
                let data = JSON.parse(event.data);
                if (data.hasOwnProperty("error")) {
                    page.message(data["error"], "error")
                }
                if (data.hasOwnProperty("info")) {
                    page.message(data["info"] + "info")
                }
                if (data.hasOwnProperty("success")) {
                    console.log('getSensorDataStream:', event.data);
                    page.message(data["success"], "info")
                }
            }
            console.log('getSensorDataStream:', event.data);
        });

        eventSource.addEventListener('error', (event) => {
            console.log("error:", event);
            eventSource.close();
            page.message('EventSource "getSensorDataStream" connection closed.', 'error');
        });

    },

    // get sensor data
    getSensorData: function(sname, calback) {
        $.ajax({
            url: server.url + "/sensordata",
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ "id": sensor.id }),
            async: sensor.async,
            timeout: sensor.timeout,
            cache: false,
            dataType: 'json',
            success: function(data, textStatus, jqXHR) {
                if (typeof(data) === undefined || data == null) {
                    console.log("sensordata: no response")
                    page.message("Could not load sensordata", "error")
                } else {
                    if (data.hasOwnProperty("error") && typeof(data["error"]) === "string") {
                        page.message(data["error"], "error")
                        sensor.error();
                        console.log("sensordata:", data["error"])
                    }
                    if (data.hasOwnProperty("info")) {
                        //page.message(data["info"], "info")
                        sensor.info(data["info"]);
                        console.log("sensordata:", data["info"])
                    }
                    if (data.hasOwnProperty("success")) {
                        //console.log("sensordata:", data)
                        sensor.data_error = 0;
                        sensor.setSensorData(data, "scd30");
                    }
                }
            },
            error: function(jqXHR, textStatus, errorThrown) {
                sensor.data_error++;
                console.log("getSensordata: ", errorThrown);
            },
            complete: function() {
                console.log('getSensordata: complete');
            }
        });
    },

    // set data values
    setSensorData: function(data, sensor) {
        let obj = document.getElementById(sensor);
        Object.entries(data).forEach(([key, value]) => {
            let item = obj.querySelector("." + key);
            let progress = obj.querySelector(".progress-" + key);
            if (item) {
                item.innerHTML = value;
            }
            if (progress) {
                let width = 0;
                switch (key) {
                    case "temp":
                        width = value + 50;
                        progress.setAttribute("aria-valuenow", value);
                        progress.style.width = width + '%';
                        break;
                    case "relh":
                        progress.setAttribute("aria-valuenow", value);
                        progress.style.width = value + '%';
                        break;
                    case "co2":
                        let score = this.score.co2(value);
                        let state = obj.querySelector("." + key + "-state");
                        state.innerHTML = score.label;
                        removeClassWildcard($(progress), "bg-*");
                        removeClassWildcard($(state), "text-*");
                        progress.setAttribute("aria-valuenow", value);
                        progress.style.width = score.percent + '%';
                        progress.classList.add("bg-" + score.cls)
                        state.classList.add("text-" + score.cls)
                        break;
                }
            }
        });
    },

    score: {
        co2: function(value) {
            let base = 400;
            let score = new Object();

            score.label = "UNKNOWN";
            score.lvl = -1;
            score.percent = 0;
            score.cls = "light";

            if (value > 0 && value < base) {
                score.percent = value / (base / 100);
                score.lvl = 0;
                score.label = "GREAT";
            }
            if (value >= base && value <= 800) {
                score.percent = (value - base) / ((1000 - base) / 100)
                score.lvl = 1;
                score.label = "GOOD";
            }
            if (value >= 800 && value <= 1000) {
                score.percent = (value - base) / ((1000 - base) / 100)
                score.lvl = 1;
                score.label = "NORMAL";
            }
            if (value > 1000 && value <= 1600) {
                score.percent = (value - base) / ((1600 - base) / 100)
                score.lvl = 2;
                score.label = "WARNING";
            }
            if (value > 1600 && value <= 5000) {
                score.percent = (value - base) / ((5000 - base) / 100)
                score.label = "DANGER";
                score.lvl = 3;
            }
            if (value < 0 || value > 5000) {
                score.percent = 0;
                score.label = "VALUE OUT OF RANGE";
                score.lvl = -1;
            }
            switch (score.lvl) {
                case 0:
                    score.cls = "success"
                    break;
                case 1:
                    score.cls = "success"
                    break;
                case 2:
                    score.cls = "warning"
                    break;
                case 3:
                    score.cls = "danger"
                    break;
            }
            return score;
        }
    }

}

// $(document).ready(function() {
server.ap();
if (server.connected == false) server.base();
page.init();
// });