const M3U8_URL = 'https://goodspeedwang.github.io/radio.m3u8';

const audioPlayer = document.getElementById('audio-player');
const stationContainer = document.getElementById('station-container');
const currentStationName = document.getElementById('current-station-name');
const currentStationLogo = document.getElementById('current-station-logo');
const currentStationDesc = document.getElementById('current-station-desc');
const playerContainer = document.getElementById('player-container');

async function fetchM3U8(url) {
    const response = await fetch(url);
    const text = await response.text();
    return text.split('\n');
}

function parseM3U8(lines) {
    const groups = {};
    let currentStation = {};

    for (const line of lines) {
        if (line.startsWith('#EXTINF:')) {
            const match = line.match(/tvg-logo="([^"]*)"[^,]*,(.*)/);
            const groupMatch = line.match(/group-title="([^"]*)"/);

            if (match && groupMatch) {
                currentStation.logo = match[1];
                currentStation.name = match[2];
                currentStation.group = groupMatch[1];
                currentStation.desc = "正在播放";
            }
        } else if (line.trim() && !line.startsWith('#')) {
            currentStation.url = line.trim();
            if (!groups[currentStation.group]) {
                groups[currentStation.group] = [];
            }
            groups[currentStation.group].push(currentStation);
            currentStation = {};
        }
    }

    return groups;
}

let hls = null;

function updateCurrentStation(station) {
    currentStationName.textContent = station.name;
    currentStationLogo.src = station.logo;
    currentStationDesc.textContent = station.desc || '';

    // **新增：动态修改浏览器标签标题**
    document.title = `${station.name}`;

    // 显示播放器
    playerContainer.style.display = 'flex';

    if (hls) {
        hls.destroy();
        hls = null;
    }

    if (station.url.endsWith('.m3u8')) {
        if (Hls.isSupported()) {
            hls = new Hls();
            hls.loadSource(station.url);
            hls.attachMedia(audioPlayer);
            hls.on(Hls.Events.MANIFEST_PARSED, () => {
                audioPlayer.play();
            });
        } else {
            audioPlayer.src = station.url;
            audioPlayer.play();
        }
    } else {
        audioPlayer.src = station.url;
        audioPlayer.play();
    }
}

function createStationElement(station) {
    const el = document.createElement('div');
    el.className = 'station';
    el.innerHTML = `
        <img src="${station.logo}">
        <p>${station.name}</p>
    `;
    el.addEventListener('click', () => updateCurrentStation(station));
    return el;
}

function createGroupElement(title, stations) {
    const container = document.createElement('div');

    const titleEl = document.createElement('h2');
    titleEl.className = 'group-title';
    titleEl.textContent = title;

    const list = document.createElement('div');
    list.className = 'station-list';

    stations.forEach(st => list.appendChild(createStationElement(st)));

    container.appendChild(titleEl);
    container.appendChild(list);
    return container;
}

async function initializePlayer() {
    const m3u8Content = await fetchM3U8(M3U8_URL);
    const groups = parseM3U8(m3u8Content);

    Object.keys(groups).forEach(title => {
        stationContainer.appendChild(createGroupElement(title, groups[title]));
    });
}

initializePlayer();
