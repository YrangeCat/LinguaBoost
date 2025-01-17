// static/scripts.js
const ANKI_VERSION = 6;

// Cache frequently accessed elements
const tooltip = document.createElement('div');
tooltip.id = 'customTooltip';
tooltip.classList.add('custom-tooltip');
document.body.appendChild(tooltip);

let isAddingToAnki = false;
let isSettingsPanelInitialized = false;

// --- Helper Functions ---
const translationButton = document.getElementById('translation-button');
translationButton.addEventListener('click', function() {
  // 执行复制翻译的操作，例如：
  copyTranslation(); 
});

function copyTranslation() {
  const text = document.getElementById("translation-content").innerText;

  // 创建一个临时的 textarea 元素
  const tempTextArea = document.createElement("textarea");
  tempTextArea.value = text;
  // 隐藏 textarea
  tempTextArea.style.position = 'absolute';
  tempTextArea.style.left = '-9999px'; // 移出可视区域
  document.body.appendChild(tempTextArea);

  // 选中并复制文本
  tempTextArea.select();
  tempTextArea.setSelectionRange(0, 99999); // For mobile devices

  try {
    document.execCommand('copy');
     console.log("翻译已复制到剪贴板！");
      const element = document.getElementById("translation-content");
              element.style.opacity = 0.5;
              setTimeout(() => {
                element.style.opacity = 1;
              }, 200);
  } catch (err) {
    console.error("复制失败: ", err);
  }
  // 移除临时的 textarea 元素
  document.body.removeChild(tempTextArea);
}

function toggleSettings() {
    const settingsPanel = document.getElementById('settings-panel');
    const isPanelVisible = settingsPanel.style.display === 'block';
    settingsPanel.style.display = isPanelVisible ? 'none' : 'block';

    if (!isPanelVisible && !isSettingsPanelInitialized) {
        let activeTab = document.querySelector('.tablinks.active');
        if (!activeTab) {
            activeTab = document.querySelector('.tablinks');
        }
        activeTab.click();
        isSettingsPanelInitialized = true;
    }
}

async function loadToggleStates() {
    try {
        const response = await fetch('/get_settings');
        if (!response.ok) {
            throw new Error(`Failed to fetch settings: ${response.status}`);
        }
        const settings = await response.json();

        for (const key in settings) {
            const element = document.getElementById(key);
            if (element) {
                if (element.type === 'checkbox') {
                    element.checked = settings[key];
                } else if (element.tagName.toLowerCase() === 'select') {
                    let optionExists = Array.from(element.options).some(option => option.value === settings[key]);
                    if (optionExists) {
                        element.value = settings[key];
                    } else {
                        console.warn(`Option with value '${settings[key]}' not found in select element.`);
                    }
                } else {
                    element.value = settings[key];
                }
            }
        }
    } catch (error) {
        console.error("Error loading settings:", error);
        showCustomAlert(`Error loading settings: ${error.message}`);
    }
}

async function saveSettings() {
    const settings = {};
    const formElements = document.querySelectorAll('#settings-panel input, #settings-panel select');

    formElements.forEach(element => {
        if (element.type === 'checkbox') {
            settings[element.id] = element.checked;
        } else {
            settings[element.id] = element.value;
        }
    });

    try {
        const response = await fetch('/update_settings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(settings)
        });

        if (!response.ok) {
            throw new Error(`Failed to update settings: ${response.status}`);
        }

        const translationContent = document.getElementById('translation-content');
        if (translationContent && !settings['translationEnabled']) {
            translationContent.style.opacity = '0';
        }

        document.getElementById('settings-panel').style.display = 'none';

    } catch (error) {
        console.error("Error saving settings:", error);
        showCustomAlert(`Error saving settings: ${error.message}`);
    }
}

const alertContainer = document.getElementById('alert-container');
let hideTimeout = null;

function showCustomAlert(message) {
    if (!alertContainer) {
        console.error("Alert container not found!");
        return;
    }
    clearTimeout(hideTimeout);
    alertContainer.innerHTML = message;
    hideTimeout = setTimeout(() => {
        alertContainer.innerHTML = '';
    }, 6000);
}

async function addToAnki(word, definition, text, translation) {
    if (isAddingToAnki) {
        return;
    }

    showCustomAlert("Adding...");
    isAddingToAnki = true;

    try {
        const response = await fetch('/add_note_to_anki', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                word: word,
                definition: definition,
                context: text,
                contextTranslation: translation,
            }),
        });

        if (!response.ok) {
            const message = await response.json().then(data => data.error || response.statusText);
            throw new Error(`Failed to add note: ${response.status} - ${message}`);
        }

        const data = await response.json();
        if (data.error) {
            throw new Error(`Error adding to Anki: ${data.error}`);
        }

        showCustomAlert(`Successfully added: ${data.result}`);
    } catch (error) {
        console.error("Error adding to Anki:", error);
        showCustomAlert(`Error: ${error.message}`);
    } finally {
        isAddingToAnki = false;
    }
}

function updateTooltipPosition(target) {
    const targetRect = target.getBoundingClientRect();
    const tooltipRect = tooltip.getBoundingClientRect();
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;

    let top = targetRect.top - tooltipRect.height + window.scrollY;
    let left = targetRect.left + window.scrollX;

    if (top < window.scrollY) {
        top = targetRect.bottom + window.scrollY;
    }

    if (top + tooltipRect.height > window.scrollY + viewportHeight) {
        top = window.scrollY + viewportHeight - tooltipRect.height;
    }

    if (left + tooltipRect.width > viewportWidth) {
        left = viewportWidth - tooltipRect.width - 5;
    }

    if (left < 0) {
        left = 5;
    }

    tooltip.style.top = `${top}px`;
    tooltip.style.left = `${left}px`;
}

function showTooltip(target) {
    tooltip.innerHTML = target.getAttribute('data-definition');
    tooltip.classList.add('visible');
    tooltip.classList.remove('hidden');
    updateTooltipPosition(target);
}

function hideTooltip() {
    tooltip.classList.add('hidden');
    tooltip.classList.remove('visible');
}

function handleMouseEnter(event) {
    const target = event.target;
    if (!target.classList.contains('highlighted-term')) return;

    showTooltip(target);
}

function handleMouseLeave(event) {
    if (event.relatedTarget && (tooltip.contains(event.relatedTarget) || event.relatedTarget.closest('.highlighted-term'))) {
        return;
    }
    hideTooltip();
}

function handleClick(event) {
    const target = event.target;
    if (!target.classList.contains('highlighted-term')) return;

    event.preventDefault();

    target.style.pointerEvents = 'none';
    target.style.opacity = '0.5';

    const textContent = document.getElementById('text-content')?.textContent;
    const translationContent = document.getElementById('translation-content')?.textContent;

    addToAnki(target.textContent, target.getAttribute('data-definition'), textContent, translationContent)
        .finally(() => {
            target.style.pointerEvents = '';
            target.style.opacity = '';
            target.blur();
        });
}

function handleKeyDown(event) {
    if (event.key === 'Escape') {
        hideTooltip();
    }
}

function openTab(evt, tabName) {
    var i, tabcontent, tablinks;
    tabcontent = document.getElementsByClassName("tabcontent");
    for (i = 0; i < tabcontent.length; i++) {
        tabcontent[i].style.display = "none";
    }

    tablinks = document.getElementsByClassName("tablinks");
    for (i = 0; i < tablinks.length; i++) {
        tablinks[i].className = tablinks[i].className.replace(" active", "");
    }

    document.getElementById(tabName).style.display = "block";
    evt.currentTarget.className += " active";
}

function initialize() {
    tooltip.style.maxWidth = '20rem';
    isSettingsPanelInitialized = false;
    document.getElementById('settings-button')?.addEventListener('click', toggleSettings);

    loadToggleStates();

    document.getElementById('save-settings-button')?.addEventListener('click', saveSettings);

    document.body.addEventListener('mouseenter', handleMouseEnter, true);
    document.body.addEventListener('mouseleave', handleMouseLeave, true);
    document.body.addEventListener('click', handleClick, true);
    document.body.addEventListener('keydown', handleKeyDown, true);

    new MutationObserver(() => {
        const highlightedTerm = document.querySelector('.highlighted-term:hover');
        if (tooltip.classList.contains('visible') && highlightedTerm) {
            updateTooltipPosition(highlightedTerm);
        }
    }).observe(tooltip, { attributes: true, childList: true, subtree: true, characterData: true });

    document.getElementById('refresh-button')?.addEventListener('click', refreshContent);

    console.log('scripts.js initialized.');
}

async function refreshContent() {
    const textToTranslate = document.getElementById('text-content').textContent;
    if (!textToTranslate) {
        console.error("No text to translate found.");
        return;
    }

    try {
        showCustomAlert("正在刷新,请勿反复点击...");
        const response = await fetch(`/refresh?text=${encodeURIComponent(textToTranslate)}`);
        if (!response.ok) {
            throw new Error(`Failed to refresh content: ${response.status}`);
        }
        const html = await response.text();
        const newDocument = new DOMParser().parseFromString(html, 'text/html');

        document.querySelector('article').replaceWith(newDocument.querySelector('article'));
        document.getElementById('settings-button').replaceWith(newDocument.getElementById('settings-button'));
        document.getElementById('settings-panel').replaceWith(newDocument.getElementById('settings-panel'));
        document.getElementById('anki-config').replaceWith(newDocument.getElementById('anki-config'));
        document.getElementById('refresh-button').replaceWith(newDocument.getElementById('refresh-button'));

        initialize();
    } catch (error) {
        console.error("Error refreshing content:", error);
        showCustomAlert(`Error refreshing content: ${error.message}`);
    }
}

document.getElementById('translation-button').addEventListener('click', copyTranslation); // Add event listener

document.addEventListener('DOMContentLoaded', initialize);