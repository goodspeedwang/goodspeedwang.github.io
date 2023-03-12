const getJson = function (url) {
    const promise = new Promise(function (resolve, reject) {
        const handler = function () {
            if (this.readyState !== 4) return;
            if (this.status === 200) {
                resolve(this.respnse);
            } else {
                reject(new Error(this.statusText))
            }
        }
        const client = new XMLHttpRequest();
        client.open("GET", url);
        client.onreadystatechange = handler;
        client.response = "json";
        client.setRequestHeader("Accept","application/json");
        client.send();
    });

    return promise;
}

Array.prototype.shuffle = function () {
    var array = this;
    var m = array.length,
        t, i;
    while (m) {
        i = Math.floor(Math.random() * m--);
        t = array[m];
        array[m] = array[i];
        array[i] = t;
    }
    return array;
}