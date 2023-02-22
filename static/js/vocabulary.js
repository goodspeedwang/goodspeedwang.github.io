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

let word = data = null;

window.onload = init;
document.getElementById("test").onkeyup = function (e) {
    let input = document.getElementById("word").value.trim();
    if (e.key === 'Enter') {
        if (input === word) {
            new storage(word).increase();
            exam();
        } else {
            console.log("wrong");
            new storage(word).del();
        }
    }
    
    if (e.key > 'a' && e.key < 'z'){
        for (let index = 0; index < input.length; index++) {
            const m = input.substring(0,index+1), n = word.substring(0,index+1)
            if(m != n){
                //document.getElementById("word").setSelectionRange(0, index);
                break;
            }
        }    
    }
}

function init() {
    data = JSON.parse(JSON.stringify(DATA)).filter(x=> {
        let item = new storage(x.test.word);
        return item.number < 5
    });
    if(data.length === 0){
        console.log("FINISH");
        return;
    }
    data.shuffle();
    exam();
}

function exam() {
    if (data.length === 0) {
        init();
        return;
    }
    let item = data.pop();
    document.getElementById("explanation").innerHTML = item.explanation;
    let test = item.test;
    word = test.word;
    let sentence = test.sentence;
    sentence = sentence.replace(word, "<input id='word' />")
    document.getElementById("test").innerHTML = sentence;
    //console.log(word);
    document.getElementById("number").innerHTML = new storage(word).number;
    document.getElementById("word").focus();
    playvoice();
}



function tips() {
    document.getElementById("word").value = word;
}

class storage {
    constructor(key) {
        this.key = key;
        this.number = 0;
        this.updateTime = Date.now();
        if (localStorage.getItem(this.key)) {
            let obj = JSON.parse(localStorage.getItem(this.key));
            let now = new Date();
            let updateTime = obj.updateTime;
            if(updateTime < now.setDate(now.getDate()- 5)){
                this.del();
                return;
            }
            this.number = obj.number;
            this.updateTime = updateTime;
        }
    }
    increase() {
        var object = {
            updateTime: Date.now(),
            number: this.number + 1
        }
        localStorage.setItem(this.key, JSON.stringify(object));
    }
    del() {
        localStorage.removeItem(this.key);
    }
}

function playvoice() {
    let url = "https://dict.youdao.com/dictvoice?audio=" + word + "&type=1";
    var audio = new Audio(url);
    audio.play();
}