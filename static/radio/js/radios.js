const swiper = new Swiper('.swiper-container', {
    loop: true,
    slidesPerView: 1,
    spaceBetween: 0,
    navigation: {
        nextEl: '.swiper-button-next',
        prevEl: '.swiper-button-prev',
    },
    breakpoints: {
        640: {
            slidesPerView: 2,
            spaceBetween: 20,
        },
        992: {
            slidesPerView: 3,
            spaceBetween: 40,
        },
        1024: {
            slidesPerView: 4,
            spaceBetween: 60,
        },
        1400: {
            slidesPerView: 5,
            spaceBetween: 60,
        },
    }
});


const cards = document.querySelectorAll('.card')
const audio = new Audio();
const playBtn = document.querySelector('.play-btn');
const progressBar = document.querySelector('.progress-bar');
const currentTimeDisplay = document.querySelector('.current-time');
const totalTimeDisplay = document.querySelector('.total-time');
const radioName = document.getElementById('radio-name');
const radioCategory = document.getElementById('radio-category');
const radioImg = document.getElementById('radio-img');
const musicPlayer = document.querySelector('.music-player');
const footer = document.querySelector('footer');
let isPlaying = false;

function playAudio() {
    audio.play();
    isPlaying = true;
    playBtn.innerHTML = '<i class="fas fa-pause"></i>';
}

function pauseAudio() {
    audio.pause();
    isPlaying = false;
    playBtn.innerHTML = '<i class="fas fa-play"></i>';
}

function togglePlay() {
    isPlaying ? pauseAudio() : playAudio();
}

function updateProgressBar() {
    progressBar.value = (audio.currentTime / audio.duration) * 100;
    const minutes = Math.floor(audio.currentTime / 60);
    const seconds = Math.floor(audio.currentTime % 60);
    currentTimeDisplay.innerText = `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
}

function setTotalTime() {
    // const minutes = Math.floor(audio.duration / 60);
    // const seconds = Math.floor(audio.duration % 60);
    // totalTimeDisplay.innerText = `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
    totalTimeDisplay.innerText = "-";
}

playBtn.addEventListener('click', togglePlay);
audio.addEventListener('timeupdate', updateProgressBar);
audio.addEventListener('loadedmetadata', setTotalTime);
progressBar.addEventListener('input', () => {
    audio.currentTime = (progressBar.value / 100) * audio.duration;
});


function updateMusicPlayerPosition() {
    // const footerHeight = footer.offsetHeight;
    const visibleFooterHeight = window.innerHeight + window.scrollY - footer.offsetTop;
    const musicPlayerBottom = visibleFooterHeight < 0 ? 0 : visibleFooterHeight;
    musicPlayer.style.bottom = `${musicPlayerBottom}px`;
}
window.addEventListener('scroll', updateMusicPlayerPosition);
window.addEventListener('resize', updateMusicPlayerPosition);

cards.forEach(card => {
   card.addEventListener('click', ev => {
       cards.forEach(el => {el.classList.remove('active')})
       card.classList.add('active')
       musicPlayer.classList.remove('d-none')
       updateRadioInfo(card.dataset.category, card.dataset.name, card.dataset.img, card.dataset.url)
   })
});

function updateRadioInfo(category, name, img, stream_url){
    radioCategory.innerHTML = category ? category : "";
    radioName.innerHTML = name;
    radioImg.setAttribute('src', img);
    audio.src = stream_url;
    togglePlay()

}