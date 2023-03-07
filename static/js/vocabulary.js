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
const stats = { right: 0, wrong: 0 };
window.onload = init;
document.getElementById("test").onkeyup = function (e) {
    let input = document.getElementById("word").value.trim();
    if (e.key === 'Enter') {
        if (input === word) {
            new storage(word).increase();
            stats.right++;
            exam();
        } else {
            stats.wrong++;
            new storage(word).del();
        }
    }

    if (e.key > 'a' && e.key < 'z') {
        for (let index = 0; index < input.length; index++) {
            const m = input.substring(0, index + 1), n = word.substring(0, index + 1)
            if (m != n) {
                //document.getElementById("word").setSelectionRange(0, index);
                break;
            }
        }
    }
}

function init() {
    data = JSON.parse(JSON.stringify(DATA)).filter(x => {
        if(!x.test || !x.test.word) return false;
        let item = new storage(x.test.word);
        //return true;
        return item.number < 5
    });
    //console.log(data.map(x=>"\""+x.test.word+"\"").join(","))
    
    if (data.length === 0) {
        console.log("FINISH");
        return;
    }
    console.log(data.length);
    stats.wrong = stats.right = 0;
    data.shuffle();
    exam();
}

function exam() {
    if (data.length === 0) {
        init();
        return;
    }
    let item = data.pop();
    if(document.getElementById("explanation_show").checked){
        document.getElementById("explanation").innerHTML = item.explanation;
    }else{
        document.getElementById("explanation").innerHTML = "";
    }
    let test = item.test;
    word = test.word;
    let sentence = "<input id='word' />";
    if(document.getElementById("sentence_show").checked){
        sentence = test.sentence.replace(word, "<input id='word' />")
    }
    document.getElementById("test").innerHTML = sentence;
    //console.log(word);
    document.getElementById("number").innerHTML = new storage(word).number;
    document.getElementById("stats").innerHTML = stats.right + " vs " + stats.wrong;
    document.getElementById("word").focus();
    if(document.getElementById("autoplay_show").checked){
        playvoice();
    }   
}

function tips() {
    document.getElementById("word").value = word;
}

class storage {
    constructor(key) {
        this.key = key + "";
        this.number = 0;
        this.updateTime = Date.now();
        if (localStorage.getItem(this.key)) {
            let obj = JSON.parse(localStorage.getItem(this.key));
            let now = new Date();
            let updateTime = obj.updateTime;
            if (updateTime < now.setDate(now.getDate() - 5)) {
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