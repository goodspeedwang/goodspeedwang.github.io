const passwordLength = 16;
function genPassword() {
    let chars = "abcdefghijklmnopqrstuvwxyz".split("");
    if (document.getElementById("numbers").checked) {
        chars = chars.concat("0123456789".split(""));
    }
    if (document.getElementById("symbols").checked) {
        chars = chars.concat("~!@#$%^&*()<>[]{}".split(""));
    }
    if (document.getElementById("uppercase").checked) {
        chars = chars.concat("ABCDEFGHIJKLMNOPQRSTUVWXYZ".split(""));
    }
    document.getElementById("password").value = Array
        .from(new Array(passwordLength).keys())
        .map(x => chars[Math.floor(Math.random() * chars.length)])
        .join("");
}

function copyPassword() {
    let copyText = document.getElementById("password");
    copyText.select();
    document.execCommand("copy");
}
document.body.onload = genPassword;