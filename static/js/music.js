let currentAlbum = 0;
let currentSong = 0;
let isPlaying = false;
let audio = new Audio();

const albumList = document.getElementById('album-list');
const songList = document.getElementById('song-list');
const playPauseButton = document.getElementById('play-pause');
const previousButton = document.getElementById('previous');
const nextButton = document.getElementById('next');
const progress = document.getElementById('progress');
const nowPlayingCover = document.getElementById('now-playing-cover');
const nowPlayingName = document.getElementById('now-playing-name');
const nowPlayingArtist = document.getElementById('now-playing-artist');
const playAllButton = document.getElementById('play-all');
const albumCover = document.getElementById('album-cover');
const albumTitle = document.getElementById('album-title');
const albumArtist = document.getElementById('album-artist');
const currentTimeDisplay = document.getElementById('current-time');
const durationDisplay = document.getElementById('duration');

function createAlbumList() {
    ALBUM.forEach((album, index) => {
        const li = document.createElement('li');
        li.className = 'album-item';
        li.innerHTML = `
                    <img src="${album.cover}" alt="${album.name}">
                    <span>${album.name}</span>
                `;
        li.onclick = () => showAlbum(index);
        albumList.appendChild(li);
    });
}

function showAlbum(index) {
    currentAlbum = index;
    songList.innerHTML = '';
    const album = ALBUM[index];
    albumCover.src = album.cover;
    albumTitle.textContent = album.name;
    albumArtist.textContent = album.artist;
    album.songs.forEach((song, i) => {
        const songItem = document.createElement('div');
        songItem.className = 'song-item';
        songItem.innerHTML = `
                    <div class="song-number">${i + 1}</div>
                    <div class="song-title">${song}</div>
                    <div class="song-duration" id="song-duration-${i}">loading...</div>
                `;
        songItem.onclick = () => playSong(i);
        songList.appendChild(songItem);
    });
    updateNowPlaying();
    updateAlbumListHighlight();
}

function updateAlbumListHighlight() {
    const albumItems = document.querySelectorAll('.album-item');
    albumItems.forEach((item, index) => {
        if (index === currentAlbum) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });
}
function sanitizeFileName(name) {
    // 替换常见的问题字符
    return name.replace(/\//g, "_")
}

function playSong(index) {
    currentSong = index;
    const encodedAlbumName = sanitizeFileName(ALBUM[currentAlbum].name);
    const encodedSongName = sanitizeFileName(ALBUM[currentAlbum].songs[index]);
    audio.src = `static/song/${encodedAlbumName}/${encodedSongName}.mp3`;

    // 更新浏览器标题为当前播放的歌曲名
    document.title = `${ALBUM[currentAlbum].songs[currentSong]} - ${ALBUM[currentAlbum].artist}`;
    // 检查音频文件路径是否正确
    console.log(`Playing: ${audio.src}`);

    // 保存当前专辑和歌曲索引到 localStorage
    localStorage.setItem('currentAlbum', currentAlbum);
    localStorage.setItem('currentSong', currentSong);

    audio.onloadedmetadata = () => {
        document.getElementById(`song-duration-${index}`).textContent = formatTime(audio.duration);
    };

    audio.play();
    isPlaying = true;
    updatePlayPauseButton();
    updateNowPlaying();
    updateSongListHighlight();
}

function updateSongListHighlight() {
    const songItems = document.querySelectorAll('.song-item');
    songItems.forEach((item, index) => {
        if (index === currentSong) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });
}

function updatePlayPauseButton() {
    playPauseButton.textContent = isPlaying ? '❚❚' : '▶';
}

function updateNowPlaying() {
    nowPlayingCover.src = ALBUM[currentAlbum].cover;
    nowPlayingName.textContent = ALBUM[currentAlbum].songs[currentSong];
    nowPlayingArtist.textContent = ALBUM[currentAlbum].artist;
}

function formatTime(seconds) {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${minutes}:${remainingSeconds < 10 ? '0' : ''}${remainingSeconds}`;
}

function playNextSong() {
    currentSong++;
    if (currentSong >= ALBUM[currentAlbum].songs.length) {
        currentSong = 0;
        isPlaying = false;
        updatePlayPauseButton();
    } else {
        playSong(currentSong);
    }
}

// 点击播放按钮时，如果还没有设置音频源，则开始播放上次的歌曲
playPauseButton.onclick = () => {
    if (isPlaying) {
        audio.pause();
        isPlaying = false;
    } else {
        if (!audio.src) {
            // 如果还没有加载歌曲，则从上次保存的位置开始播放
            playSong(currentSong);
        } else {
            audio.play().catch(error => {
                console.error('播放失败:', error);
            });
            isPlaying = true;
        }
    }
    updatePlayPauseButton();
};

previousButton.onclick = () => {
    currentSong = (currentSong - 1 + ALBUM[currentAlbum].songs.length) % ALBUM[currentAlbum].songs.length;
    playSong(currentSong);
};

nextButton.onclick = () => {
    playNextSong();
};

playAllButton.onclick = () => {
    currentSong = 0;
    playSong(currentSong);
};

audio.ontimeupdate = () => {
    const percent = (audio.currentTime / audio.duration) * 100;
    progress.style.width = `${percent}%`;
    currentTimeDisplay.textContent = formatTime(audio.currentTime);
};

audio.onloadedmetadata = () => {
    durationDisplay.textContent = formatTime(audio.duration);
};

audio.onended = () => {
    playNextSong();
};

createAlbumList();
//showAlbum(0);

window.onload = () => {
    const savedAlbum = localStorage.getItem('currentAlbum');
    const savedSong = localStorage.getItem('currentSong');

    if (savedAlbum !== null && savedSong !== null) {
        // 只展示上次播放的专辑和歌曲，不自动播放
        showAlbum(parseInt(savedAlbum));
        currentSong = parseInt(savedSong);
        updateNowPlaying();
        updateSongListHighlight();
    } else {
        // 如果没有保存的专辑和歌曲，则展示第一个专辑
        showAlbum(0);
    }
};