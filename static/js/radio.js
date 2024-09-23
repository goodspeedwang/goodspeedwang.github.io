const M3U8_URL = 'https://goodspeedwang.github.io/radio.m3u8';
const audioPlayer = document.getElementById('audio-player');
const stationContainer = document.getElementById('station-container');
const currentStationName = document.getElementById('current-station-name');
const currentStationLogo = document.getElementById('current-station-logo');
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
                const groupTitle = groupMatch[1];
                currentStation.logo = match[1];
                currentStation.name = match[2];
                currentStation.group = groupTitle;
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
    currentStationLogo.src = station.logo || 'default-logo.png';
    currentStationLogo.alt = station.name;

    // 显示播放器
    playerContainer.style.display = 'flex';

    // 销毁之前的 HLS 实例（如果存在）
    if (hls) {
        hls.destroy();
        hls = null; // 确保清除引用
    }

    if (station.url.endsWith('.m3u8')) {
        if (Hls.isSupported()) {
            hls = new Hls();
            hls.loadSource(station.url);
            hls.attachMedia(audioPlayer);
            hls.on(Hls.Events.MANIFEST_PARSED, function () {
                audioPlayer.play();
            });
        } else if (audioPlayer.canPlayType('application/vnd.apple.mpegurl')) {
            audioPlayer.src = station.url;
            audioPlayer.play();
        } else {
            alert('您的浏览器不支持HLS播放');
        }
    } else {
        // 对于非 m3u8 流，直接设置 audio 的 src
        audioPlayer.src = station.url;
        audioPlayer.play();
    }
}

function createStationElement(station) {
    const stationElement = document.createElement('div');
    stationElement.className = 'station';
    stationElement.innerHTML = `
                <img src="${station.logo || 'default-logo.png'}" alt="${station.name}">
                <p>${station.name}</p>
            `;
    stationElement.addEventListener('click', () => {
        updateCurrentStation(station);
    });
    return stationElement;
}

function createGroupElement(groupTitle, stations) {
    const groupContainer = document.createElement('div');
    const titleElement = document.createElement('h2');
    titleElement.className = 'group-title';
    titleElement.textContent = groupTitle;

    const stationList = document.createElement('div');
    stationList.className = 'station-list';

    stations.forEach(station => {
        stationList.appendChild(createStationElement(station));
    });

    groupContainer.appendChild(titleElement);
    groupContainer.appendChild(stationList);
    return groupContainer;
}

async function initializePlayer() {
    const m3u8Content = await fetchM3U8(M3U8_URL);
    const groups = parseM3U8(m3u8Content);

    for (const groupTitle in groups) {
        const groupElement = createGroupElement(groupTitle, groups[groupTitle]);
        stationContainer.appendChild(groupElement);
    }
}

initializePlayer();