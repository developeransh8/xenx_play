// Video player JavaScript

// Initialize Video.js player
const player = videojs('videoPlayer', {
    controls: true,
    preload: 'auto',
    fluid: true,
    playbackRates: [0.5, 1, 1.5, 2],
    controlBar: {
        children: [
            'playToggle',
            'volumePanel',
            'currentTimeDisplay',
            'timeDivider',
            'durationDisplay',
            'progressControl',
            'remainingTimeDisplay',
            'playbackRateMenuButton',
            'fullscreenToggle'
        ]
    }
});

// Audio track selector functionality
const audioSelectorBtn = document.getElementById('audioSelectorBtn');
const audioMenu = document.getElementById('audioMenu');
const audioOptions = Array.from(document.querySelectorAll('.audio-option'));
let audioTrackListBound = false;
let audioTrackChangeHandler = null;

if (audioSelectorBtn && audioMenu && audioOptions.length) {
    // Toggle audio menu
    audioSelectorBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        const isVisible = audioMenu.style.display === 'block';
        audioMenu.style.display = isVisible ? 'none' : 'block';
    });
    
    // Close menu when clicking outside
    document.addEventListener('click', (e) => {
        if (!audioMenu.contains(e.target) && e.target !== audioSelectorBtn) {
            audioMenu.style.display = 'none';
        }
    });
    
    // Handle audio track selection
    audioOptions.forEach(option => {
        option.addEventListener('click', (e) => {
            e.stopPropagation();
            const trackIndex = option.dataset.trackIndex;
            
            // Switch audio track
            const switched = switchAudioTrack(trackIndex);
            
            if (switched) {
                // Close menu
                audioMenu.style.display = 'none';
            }
        });
    });
    
    // Keyboard navigation for audio menu
    audioSelectorBtn.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            audioSelectorBtn.click();
        }
    });
    
    audioMenu.addEventListener('keydown', (e) => {
        const options = audioOptions;
        const currentIndex = options.indexOf(document.activeElement);
        
        switch(e.key) {
            case 'ArrowDown':
                e.preventDefault();
                if (currentIndex < options.length - 1) {
                    options[currentIndex + 1].focus();
                }
                break;
            case 'ArrowUp':
                e.preventDefault();
                if (currentIndex > 0) {
                    options[currentIndex - 1].focus();
                } else {
                    audioSelectorBtn.focus();
                }
                break;
            case 'Escape':
                e.preventDefault();
                audioMenu.style.display = 'none';
                audioSelectorBtn.focus();
                break;
        }
    });
}

function setActiveOption(option) {
    audioOptions.forEach(opt => opt.classList.remove('active'));
    if (option) {
        option.classList.add('active');
    }
}

function getAudioTrackList() {
    return typeof player.audioTracks === 'function' ? player.audioTracks() : null;
}

function findTrackForOption(option, trackList) {
    if (!option || !trackList) {
        return null;
    }

    const title = option.dataset.trackTitle;
    const language = option.dataset.trackLanguage;
    const index = option.dataset.trackIndex;

    let candidate = null;

    if (title) {
        for (let i = 0; i < trackList.length; i += 1) {
            const track = trackList[i];
            if (track.label === title) {
                candidate = track;
                break;
            }
        }
    }

    if (!candidate && language) {
        for (let i = 0; i < trackList.length; i += 1) {
            const track = trackList[i];
            if (track.language === language) {
                candidate = track;
                break;
            }
        }
    }

    if (!candidate && index !== undefined) {
        const idx = parseInt(index, 10);
        if (!Number.isNaN(idx) && idx >= 0 && idx < trackList.length) {
            candidate = trackList[idx];
        }
    }

    return candidate;
}

function switchAudioTrack(trackIndex) {
    const option = audioOptions.find(opt => opt.dataset.trackIndex === String(trackIndex));
    if (!option) {
        console.warn(`Audio option for index ${trackIndex} not found.`);
        return false;
    }

    const trackList = getAudioTrackList();
    if (!trackList || trackList.length === 0) {
        console.warn('Audio tracks are not available yet.');
        return false;
    }

    const targetTrack = findTrackForOption(option, trackList);
    if (!targetTrack) {
        console.warn('Unable to match audio track in player for option', option.dataset);
        return false;
    }

    for (let i = 0; i < trackList.length; i += 1) {
        const track = trackList[i];
        track.enabled = (track === targetTrack);
    }

    setActiveOption(option);
    localStorage.setItem(`audioTrack_${videoId}`, String(trackIndex));

    console.log(`Switched to audio track ${trackIndex} (${targetTrack.label || targetTrack.language || targetTrack.id})`);
    return true;
}

function syncActiveOptionWithPlayer() {
    const trackList = getAudioTrackList();
    if (!trackList || trackList.length === 0) {
        return;
    }

    for (let i = 0; i < trackList.length; i += 1) {
        const track = trackList[i];
        if (!track.enabled) {
            continue;
        }

        const matchingOption = audioOptions.find(option => {
            const title = option.dataset.trackTitle;
            const language = option.dataset.trackLanguage;
            const optionIndex = option.dataset.trackIndex;

            if (title && track.label === title) {
                return true;
            }
            if (language && track.language === language) {
                return true;
            }
            if (optionIndex !== undefined) {
                const idx = parseInt(optionIndex, 10);
                if (!Number.isNaN(idx) && idx === i) {
                    return true;
                }
            }

            return false;
        });

        if (matchingOption) {
            setActiveOption(matchingOption);
        }

        break;
    }
}

// Load saved audio track preference
function loadAudioPreference() {
    const savedTrack = localStorage.getItem(`audioTrack_${videoId}`);
    if (!savedTrack) {
        return;
    }

    const applyPreference = () => {
        const applied = switchAudioTrack(savedTrack);
        if (!applied) {
            console.warn('Preferred audio track could not be applied.');
        }
    };

    const trackList = getAudioTrackList();
    if (trackList && trackList.length > 0) {
        applyPreference();
    } else {
        player.one('loadedmetadata', applyPreference);
    }
}

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    // Ignore if typing in input field
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
        return;
    }
    
    switch(e.key) {
        case ' ':
        case 'k':
            e.preventDefault();
            if (player.paused()) {
                player.play();
            } else {
                player.pause();
            }
            break;
        case 'ArrowLeft':
            e.preventDefault();
            player.currentTime(player.currentTime() - 5);
            break;
        case 'ArrowRight':
            e.preventDefault();
            player.currentTime(player.currentTime() + 5);
            break;
        case 'f':
            e.preventDefault();
            if (player.isFullscreen()) {
                player.exitFullscreen();
            } else {
                player.requestFullscreen();
            }
            break;
        case 'm':
            e.preventDefault();
            player.muted(!player.muted());
            break;
        case 'ArrowUp':
            if (!audioMenu || audioMenu.style.display !== 'block') {
                e.preventDefault();
                const currentVolume = player.volume();
                player.volume(Math.min(1, currentVolume + 0.1));
            }
            break;
        case 'ArrowDown':
            if (!audioMenu || audioMenu.style.display !== 'block') {
                e.preventDefault();
                const currentVolume = player.volume();
                player.volume(Math.max(0, currentVolume - 0.1));
            }
            break;
    }
});

// Error handling
player.on('error', (e) => {
    console.error('Player error:', player.error());
    
    const errorDisplay = player.createEl('div', {
        className: 'vjs-error-display',
        innerHTML: '<div>Error loading video. Please try again.</div>'
    });
    
    player.el().appendChild(errorDisplay);
});

// Load audio preference when page loads
if (typeof videoId !== 'undefined') {
    loadAudioPreference();
}

// Log player events for debugging
player.on('loadstart', () => console.log('Loading started'));
player.on('loadedmetadata', () => {
    console.log('Metadata loaded');

    const trackList = getAudioTrackList();
    if (trackList && !audioTrackListBound) {
        audioTrackChangeHandler = () => syncActiveOptionWithPlayer();

        if (typeof trackList.addEventListener === 'function') {
            trackList.addEventListener('change', audioTrackChangeHandler);
        } else if (typeof trackList.on === 'function') {
            trackList.on('change', audioTrackChangeHandler);
        }

        audioTrackListBound = true;
    }

    syncActiveOptionWithPlayer();
});
player.on('canplay', () => console.log('Can play'));
player.on('playing', () => console.log('Playing'));
player.on('waiting', () => console.log('Waiting'));
