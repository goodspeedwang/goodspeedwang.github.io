const MusicPlayerApp = (() => {
    const PLAYBACK_STORAGE_KEYS = {
        albumIndex: 'currentAlbum',
        songIndex: 'currentSong',
    };

    const DEFAULT_DURATION_TEXT = '--:--';
    const audio = new Audio();
    const songDurations = typeof SONG_DURATIONS === 'object' && SONG_DURATIONS !== null ? SONG_DURATIONS : {};

    const state = {
        currentAlbumIndex: -1,
        currentSongIndex: 0,
        isPlaying: false,
    };

    const elements = {
        albumList: document.getElementById('album-list'),
        songList: document.getElementById('song-list'),
        albumCover: document.getElementById('album-cover'),
        albumTitle: document.getElementById('album-title'),
        albumArtist: document.getElementById('album-artist'),
        playAllButton: document.getElementById('play-all'),
        nowPlayingCover: document.getElementById('now-playing-cover'),
        nowPlayingName: document.getElementById('now-playing-name'),
        nowPlayingArtist: document.getElementById('now-playing-artist'),
        playPauseButton: document.getElementById('play-pause'),
        previousButton: document.getElementById('previous'),
        nextButton: document.getElementById('next'),
        progress: document.getElementById('progress'),
        currentTimeDisplay: document.getElementById('current-time'),
        durationDisplay: document.getElementById('duration'),
    };

    function initialize() {
        renderAlbumNavigation();
        bindPlayerControls();
        bindAudioEvents();
        restoreLastPlaybackState();
    }

    function bindPlayerControls() {
        elements.playPauseButton.addEventListener('click', handlePlayPauseClick);
        elements.previousButton.addEventListener('click', playPreviousSong);
        elements.nextButton.addEventListener('click', playNextSong);
        elements.playAllButton.addEventListener('click', playAlbumFromStart);
    }

    function bindAudioEvents() {
        audio.ontimeupdate = handleAudioTimeUpdate;
        audio.onloadedmetadata = handleAudioMetadataLoaded;
        audio.onended = playNextSong;
    }

    function restoreLastPlaybackState() {
        const savedAlbumIndex = Number.parseInt(localStorage.getItem(PLAYBACK_STORAGE_KEYS.albumIndex), 10);
        const savedSongIndex = Number.parseInt(localStorage.getItem(PLAYBACK_STORAGE_KEYS.songIndex), 10);

        if (Number.isInteger(savedAlbumIndex) && isValidAlbumIndex(savedAlbumIndex)) {
            showAlbum(savedAlbumIndex);

            if (Number.isInteger(savedSongIndex) && isValidSongIndex(savedAlbumIndex, savedSongIndex)) {
                state.currentSongIndex = savedSongIndex;
            }

            refreshNowPlayingPanel();
            updateSongSelectionHighlight();
            return;
        }

        showAlbum(0);
    }

    function renderAlbumNavigation() {
        const albumListFragment = document.createDocumentFragment();

        ALBUM.forEach((album, albumIndex) => {
            const albumItem = document.createElement('li');
            albumItem.className = 'album-item';
            albumItem.innerHTML = `
                <img src="${album.cover}" alt="${album.name}">
                <span>${album.name}</span>
            `;
            albumItem.addEventListener('click', () => showAlbum(albumIndex));
            albumListFragment.appendChild(albumItem);
        });

        elements.albumList.replaceChildren(albumListFragment);
    }

    function showAlbum(albumIndex) {
        if (!isValidAlbumIndex(albumIndex) || state.currentAlbumIndex === albumIndex) {
            return;
        }

        state.currentAlbumIndex = albumIndex;
        state.currentSongIndex = 0;

        renderAlbumDetails();
        renderSongList();
        refreshNowPlayingPanel();
        updateAlbumSelectionHighlight();
        updateSongSelectionHighlight();
    }

    function renderAlbumDetails() {
        const currentAlbum = getCurrentAlbum();
        elements.albumCover.src = currentAlbum.cover;
        elements.albumTitle.textContent = currentAlbum.name;
        elements.albumArtist.textContent = currentAlbum.artist;
    }

    function renderSongList() {
        const currentAlbum = getCurrentAlbum();
        const songListFragment = document.createDocumentFragment();

        currentAlbum.songs.forEach((songName, songIndex) => {
            const songItem = document.createElement('div');
            songItem.className = 'song-item';
            songItem.innerHTML = `
                <div class="song-number">${songIndex + 1}</div>
                <div class="song-title">${songName}</div>
                <div class="song-duration" id="${buildSongDurationElementId(songIndex)}">${getKnownSongDuration(currentAlbum.name, songName) || DEFAULT_DURATION_TEXT}</div>
            `;
            songItem.addEventListener('click', () => playSong(songIndex));
            songListFragment.appendChild(songItem);
        });

        elements.songList.replaceChildren(songListFragment);
    }

    function playSong(songIndex) {
        if (!isValidSongIndex(state.currentAlbumIndex, songIndex)) {
            return;
        }

        state.currentSongIndex = songIndex;

        const currentAlbum = getCurrentAlbum();
        const currentSong = getCurrentSongName();
        audio.src = `songs/${buildSongFilePath(currentAlbum.name, currentSong)}`;

        syncDocumentTitle();
        persistPlaybackState();
        refreshNowPlayingPanel();
        updateSongSelectionHighlight();

        audio.play().then(() => {
            state.isPlaying = true;
            updatePlayPauseButton();
        }).catch((error) => {
            state.isPlaying = false;
            updatePlayPauseButton();
            console.error('播放失败:', error);
        });
    }

    function playNextSong() {
        const nextSongIndex = state.currentSongIndex + 1;
        if (isValidSongIndex(state.currentAlbumIndex, nextSongIndex)) {
            playSong(nextSongIndex);
            return;
        }

        const nextAlbumIndex = (state.currentAlbumIndex + 1) % ALBUM.length;
        showAlbum(nextAlbumIndex);
        playSong(0);
    }

    function playPreviousSong() {
        const previousSongIndex = (state.currentSongIndex - 1 + getCurrentAlbum().songs.length) % getCurrentAlbum().songs.length;
        playSong(previousSongIndex);
    }

    function playAlbumFromStart() {
        playSong(0);
    }

    function handlePlayPauseClick() {
        if (!audio.src) {
            playSong(state.currentSongIndex);
            return;
        }

        if (state.isPlaying) {
            audio.pause();
            state.isPlaying = false;
        } else {
            audio.play().then(() => {
                state.isPlaying = true;
                updatePlayPauseButton();
            }).catch((error) => {
                console.error('播放失败:', error);
            });
            return;
        }

        updatePlayPauseButton();
    }

    function handleAudioTimeUpdate() {
        const duration = Number.isFinite(audio.duration) ? audio.duration : 0;
        const progressPercent = duration > 0 ? (audio.currentTime / duration) * 100 : 0;
        elements.progress.style.width = `${progressPercent}%`;
        elements.currentTimeDisplay.textContent = formatTime(audio.currentTime);
    }

    function handleAudioMetadataLoaded() {
        const formattedDuration = formatTime(audio.duration);
        updateSongDurationLabel(state.currentSongIndex, formattedDuration);
        updateDurationDisplay(formattedDuration);
    }

    function refreshNowPlayingPanel() {
        const currentAlbum = getCurrentAlbum();
        const currentSong = getCurrentSongName();

        elements.nowPlayingCover.src = currentAlbum.cover;
        elements.nowPlayingName.textContent = currentSong;
        elements.nowPlayingArtist.textContent = currentAlbum.artist;

        updateDurationDisplay(getKnownSongDuration(currentAlbum.name, currentSong));
        updatePlayPauseButton();
    }

    function updateAlbumSelectionHighlight() {
        const albumItems = elements.albumList.querySelectorAll('.album-item');

        albumItems.forEach((albumItem, albumIndex) => {
            const isActive = albumIndex === state.currentAlbumIndex;
            albumItem.classList.toggle('active', isActive);

            if (isActive) {
                requestAnimationFrame(() => {
                    albumItem.scrollIntoView({ behavior: 'instant', block: 'center' });
                });
            }
        });
    }

    function updateSongSelectionHighlight() {
        const songItems = elements.songList.querySelectorAll('.song-item');

        songItems.forEach((songItem, songIndex) => {
            songItem.classList.toggle('active', songIndex === state.currentSongIndex);
        });
    }

    function updatePlayPauseButton() {
        elements.playPauseButton.textContent = state.isPlaying ? '❚❚' : '▶';
    }

    function updateDurationDisplay(durationText) {
        elements.durationDisplay.textContent = durationText || DEFAULT_DURATION_TEXT;
    }

    function updateSongDurationLabel(songIndex, durationText) {
        const durationElement = document.getElementById(buildSongDurationElementId(songIndex));
        if (durationElement) {
            durationElement.textContent = durationText;
        }
    }

    function persistPlaybackState() {
        localStorage.setItem(PLAYBACK_STORAGE_KEYS.albumIndex, state.currentAlbumIndex);
        localStorage.setItem(PLAYBACK_STORAGE_KEYS.songIndex, state.currentSongIndex);
    }

    function syncDocumentTitle() {
        const currentAlbum = getCurrentAlbum();
        document.title = `${getCurrentSongName()} - ${currentAlbum.artist}`;
    }

    function buildSongFilePath(albumName, songName) {
        return `${sanitizeFileName(albumName)}/${sanitizeFileName(songName)}.mp3`;
    }

    function getKnownSongDuration(albumName, songName) {
        return songDurations[buildSongFilePath(albumName, songName)] || '';
    }

    function buildSongDurationElementId(songIndex) {
        return `song-duration-${songIndex}`;
    }

    function getCurrentAlbum() {
        return ALBUM[state.currentAlbumIndex];
    }

    function getCurrentSongName() {
        return getCurrentAlbum().songs[state.currentSongIndex];
    }

    function isValidAlbumIndex(albumIndex) {
        return Number.isInteger(albumIndex) && albumIndex >= 0 && albumIndex < ALBUM.length;
    }

    function isValidSongIndex(albumIndex, songIndex) {
        if (!isValidAlbumIndex(albumIndex)) {
            return false;
        }

        return Number.isInteger(songIndex) && songIndex >= 0 && songIndex < ALBUM[albumIndex].songs.length;
    }

    function sanitizeFileName(name) {
        // 音频文件目录里用下划线替代了路径分隔符，这里保持一致。
        return name.replace(/\//g, '_');
    }

    function formatTime(seconds) {
        const safeSeconds = Number.isFinite(seconds) ? Math.max(0, Math.floor(seconds)) : 0;
        const minutes = Math.floor(safeSeconds / 60);
        const remainingSeconds = safeSeconds % 60;
        return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
    }

    return { initialize };
})();

// 通过模块封装播放器状态，避免渲染逻辑和播放控制互相穿插。
MusicPlayerApp.initialize();
