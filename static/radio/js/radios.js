
// start render radios //
const radiosContainer = document.getElementById("radios-container");
const audio = new Audio();
let playButtons = document.querySelectorAll('.play-btn');
let activeCard = document.querySelector('.radio-card.active') || document.createElement('div');

function tag(tag){ return `<li class="tag">${tag}</li>` }

function renderTags(tags) {
    return `${tags.map( tag => { return `<li class="tag">${tag}</li>` }).join(" ")}`
}

function renderRadio(radio) {
    let is_active = audio.src.toLowerCase().trim() === radio.src.toLowerCase().trim()
    let radio_class = is_active ? ' radio-card active' : ' radio-card'
    return `
           <div class="col-12 p-3 my-2 ${radio_class}">
        
                <div class="radio-info">
                    <img class="radio-img" src="${radio.img}" alt="radio image">
                    <div class="info mx-3">
                        <p class="name">${radio.name}</p>
                        <ul class="tags">
                            ${renderTags(radio.tags)}
                        </ul>
                    </div>
                </div>
        
                <div class="play-btn ${!is_active? 'play' : audio.paused? 'play' : 'pause'}" data-src="${radio.src}"></div>
           </div>

    `

}

function renderRadiosList(radiosList) {
    if (radiosList.length > 0) {
        radiosContainer.innerHTML = radiosList.map(renderRadio).join("\n")
        playButtons = document.querySelectorAll('.play-btn');
        activeCard = document.querySelector('.radio-card.active');
        if (activeCard === null) {} else setTopToParentOffset(activeCard)

        // This block of code should be in audio control section
        playButtons.forEach(btn => {
            btn.addEventListener('click', ev => {
                if (btn.classList.contains('play')) {
                    playButtons.forEach(btn => {
                        btn.classList.remove('pause');
                        btn.classList.add('play');
                    })
                    ev.target.classList.remove('play')
                    ev.target.classList.add('pause')

                    activeCard.classList.remove('active')
                    ev.target.parentElement.classList.add('active')
                    activeCard = document.querySelector('.radio-card.active');
                    setTopToParentOffset(activeCard)
                } else {
                    playButtons.forEach(btn => {
                        btn.classList.remove('pause');
                        btn.classList.add('play');
                    })
                    ev.target.classList.remove('pause')
                    ev.target.classList.add('play')
                }

                if (audio.src.toLowerCase() === btn.dataset.src.toLowerCase()) {
                    togglePlay()
                } else {
                    setAudioSource(btn.dataset.src)
                    playAudio()
                }
            })
        })
    } else {
        radiosContainer.innerHTML = `<p style='font-size: 2rem;font-weight: bold;text-align: center; margin-top: 5rem;'>نأسف!... لم نستطع العثور علي نتائج مطابقة لبحثك</p>`
    }
}

renderRadiosList(radios)


// end render radios //

// start search //
const searchBar = document.getElementById("search")
function search(query, list) {
    query = query.trim().toLowerCase(); // Convert query to lowercase and remove leading/trailing spaces
    return list.filter(radio => {
        // Check if any of the radio's properties match the query
        return radio.name.toLowerCase().includes(query) ||
            radio.tags.some(tag => tag.toLowerCase().includes(query));
    });
}

searchBar.addEventListener("input", ()=> { renderRadiosList(search(searchBar.value, radios)) })

// end search //

// start audio controls //
let isPlaying = false;
activeCard = document.querySelector('.radio-card.active') || document.createElement('div');


function playAudio() {
    audio.play();
    isPlaying = true;
}

function pauseAudio() {
    audio.pause();
    isPlaying = false;
}

function togglePlay() {
    isPlaying ? pauseAudio() : playAudio();
}

function setAudioSource(src) {
    audio.src = src
}

function setTopToParentOffset(element) {
    // Get the parent element
    const parent = element.parentElement.parentElement;
    element.style.width = window.innerWidth < 768? (parent.offsetWidth - 32) + 'px': parent.offsetWidth + 'px';

    // Get the parent's y-offset
    const parentY = parent.getBoundingClientRect().y;

    if (parentY < 0)
    {
        element.style.top = window.scrollY + 'px';
    }
    else
    {
        element.style.top = parentY + 'px';

        const emptyDiv = document.createElement('div');
        if (!parent.firstElementChild.classList.contains("emptyDiv") )
        {
            emptyDiv.style.height = activeCard.offsetHeight + 14 + 'px';
            emptyDiv.classList.add('emptyDiv')
            parent.insertBefore(emptyDiv, parent.firstChild);
        }
    }
}


window.addEventListener('scroll', () => setTopToParentOffset(activeCard));


// end audio controls //
