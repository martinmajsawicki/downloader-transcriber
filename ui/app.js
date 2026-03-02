/* ═══════════════════════════════════════════════════
   Copysight — Frontend Logic
   Navigation, pywebview bridge, pipeline, library
   ═══════════════════════════════════════════════════ */

// ── State ──
let currentScreen = 'input';
let pollInterval = null;
let lastStampCount = 0;
let lastStampTexts = [];

// ── Typewriter state ──
let stampQueue = [];
let isTyping = false;
let currentTypingEl = null;
let dotsTimer = null;
let staleTimer = null;
let lastUpdateTime = 0;

// ── Reader state ──
let rawReaderMarkdown = '';

// ── DOM refs ──
const screens = {
  input: document.getElementById('screen-input'),
  reader: document.getElementById('screen-reader'),
  library: document.getElementById('screen-library'),
};

const urlInput = document.getElementById('urlInput');
const goBtn = document.getElementById('goBtn');
const stampArea = document.getElementById('stampArea');
const soundWave = document.getElementById('soundWave');
const settingsTrigger = document.getElementById('settingsTrigger');
const settingsOverlay = document.getElementById('settingsOverlay');
const settingsPanel = document.getElementById('settingsPanel');
const settingsDone = document.getElementById('settingsDone');
const videoMeta = document.getElementById('videoMeta');
const dateStamp = document.getElementById('dateStamp');
const readerArticle = document.getElementById('readerArticle');
const newBtn = document.getElementById('newBtn');
const copyBtn = document.getElementById('copyBtn');
const exportBtn = document.getElementById('exportBtn');
const fileList = document.getElementById('fileList');
const searchBar = document.getElementById('searchBar');

// Settings fields
const apiKeyInput = document.getElementById('apiKeyInput');
const apiKeyStatus = document.getElementById('apiKeyStatus');
const langSelect = document.getElementById('langSelect');
const modelSelect = document.getElementById('modelSelect');
const contextInput = document.getElementById('contextInput');
const analysisPrompt = document.getElementById('analysisPrompt');


// ═══════════════════════════════════════
//  NAVIGATION
// ═══════════════════════════════════════

function navigateTo(screenId) {
  if (!screens[screenId]) return;
  currentScreen = screenId;

  Object.values(screens).forEach(function(s) {
    s.classList.remove('active', 'fade-in');
  });

  var target = screens[screenId];
  target.classList.add('active', 'fade-in');

  // Load library data when navigating to library
  if (screenId === 'library') {
    loadLibrary();
  }
}

// Nav hint click handlers
document.querySelectorAll('.nav-hint').forEach(function(hint) {
  hint.addEventListener('click', function() {
    var target = this.getAttribute('data-target');
    if (target) navigateTo(target);
  });
});

// Keyboard navigation: arrows between reader and library
document.addEventListener('keydown', function(e) {
  if (settingsOverlay && !settingsOverlay.classList.contains('hidden')) {
    if (e.key === 'Escape') closeSettings();
    return;
  }

  if (e.key === 'ArrowLeft' && currentScreen === 'input') {
    navigateTo('library');
  } else if (e.key === 'ArrowLeft' && currentScreen === 'reader') {
    navigateTo('library');
  } else if (e.key === 'ArrowRight' && currentScreen === 'library') {
    navigateTo('reader');
  } else if (e.key === 'Escape' && currentScreen !== 'input') {
    stopPipeline();
    navigateTo('input');
  }
});


// ═══════════════════════════════════════
//  PIPELINE
// ═══════════════════════════════════════

function stopPipeline() {
  if (pollInterval) {
    clearInterval(pollInterval);
    pollInterval = null;
  }
  stopDots();
  soundWave.classList.remove('active');
  goBtn.classList.remove('busy');
  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.cancel_pipeline().catch(function() {});
  }
}

goBtn.addEventListener('click', startPipeline);

urlInput.addEventListener('keydown', function(e) {
  if (e.key === 'Enter') startPipeline();
});

function startPipeline() {
  var url = urlInput.value.trim();
  if (!url) {
    urlInput.classList.add('shake');
    setTimeout(function() { urlInput.classList.remove('shake'); }, 500);
    return;
  }

  // Prevent double-start
  if (goBtn.classList.contains('busy')) return;
  goBtn.classList.add('busy');

  // Clear previous stamps
  while (stampArea.firstChild) {
    stampArea.removeChild(stampArea.firstChild);
  }
  lastStampCount = 0;
  lastStampTexts = [];
  stampQueue = [];
  isTyping = false;
  currentTypingEl = null;
  stopDots();
  soundWave.classList.add('active');

  // Hide tagline during processing
  var tagline = document.getElementById('brandTagline');
  if (tagline) tagline.classList.add('hidden');

  // Call Python backend
  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.start_pipeline(url).then(function(result) {
      if (result && result.started) {
        pollInterval = setInterval(pollPipelineStatus, 500);
      } else {
        queueStampTypewriter('Error: ' + (result && result.reason || 'Unknown'));
        soundWave.classList.remove('active');
        goBtn.classList.remove('busy');
      }
    }).catch(function() {
      queueStampTypewriter('Error: bridge failure');
      soundWave.classList.remove('active');
      goBtn.classList.remove('busy');
    });
  } else {
    // Fallback for testing without pywebview
    queueStampTypewriter('Connecting...');
    setTimeout(function() { queueStampTypewriter('Downloading...'); }, 2000);
    setTimeout(function() { queueStampTypewriter('Transcribing...'); }, 4500);
    setTimeout(function() { queueStampTypewriter('Analyzing...'); }, 7000);
    setTimeout(function() {
      soundWave.classList.remove('active');
      queueStampTypewriter('Done.');
    }, 9000);
  }
}

function pollPipelineStatus() {
  if (!window.pywebview || !window.pywebview.api) return;

  window.pywebview.api.get_pipeline_status().then(function(status) {
    if (!status) return;
    var stamps = status.stamps || [];

    // Keep dots alive while pipeline is active (polling proves app is responsive)
    if (status.step !== 'idle' && status.step !== 'done' && status.step !== 'error') {
      lastUpdateTime = Date.now();
    }

    // Check if last known stamp was updated in place (progress callbacks)
    if (lastStampCount > 0 && stamps.length >= lastStampCount) {
      var lastIdx = lastStampCount - 1;
      if (stamps[lastIdx] !== lastStampTexts[lastIdx]) {
        updateLastStampText(stamps[lastIdx]);
        lastStampTexts[lastIdx] = stamps[lastIdx];
      }
    }

    // Add new stamps
    while (lastStampCount < stamps.length) {
      queueStampTypewriter(stamps[lastStampCount]);
      lastStampTexts.push(stamps[lastStampCount]);
      lastStampCount++;
    }

    // Check if done
    if (status.done) {
      clearInterval(pollInterval);
      pollInterval = null;
      soundWave.classList.remove('active');
      goBtn.classList.remove('busy');

      // Fetch result and transition to reader
      window.pywebview.api.get_result().then(function(result) {
        if (result) {
          populateReader(result.analysis || result.transcript || '', result.meta);
          setTimeout(function() {
            fadeStamps();
            setTimeout(function() {
              navigateTo('reader');
            }, 400);
          }, 800);
        }
      }).catch(function() {
        queueStampTypewriter('Error: could not fetch result');
      });
    } else if (status.step === 'error' || status.step === 'idle') {
      clearInterval(pollInterval);
      pollInterval = null;
      soundWave.classList.remove('active');
      goBtn.classList.remove('busy');
    }
  }).catch(function() {
    stopPipeline();
    queueStampTypewriter('Error: bridge failure');
  });
}

// ── Typewriter engine ──

function queueStampTypewriter(text) {
  stampQueue.push(text);
  if (!isTyping) processStampQueue();
}

function processStampQueue() {
  if (stampQueue.length === 0) {
    isTyping = false;
    return;
  }

  isTyping = true;
  stopDots();

  var text = stampQueue.shift();
  var line = document.createElement('div');
  line.className = 'stamp-line typing';
  line.textContent = '';
  stampArea.appendChild(line);
  currentTypingEl = line;

  typeText(line, text, 0, function() {
    line.classList.remove('typing');
    // If ends with "...", start cycling dots
    if (text.endsWith('...')) {
      startDots(line, text.slice(0, -3));
    }
    processStampQueue();
  });
}

function typeText(el, text, idx, callback) {
  if (idx >= text.length) {
    callback();
    return;
  }
  el.textContent = text.substring(0, idx + 1);
  var delay = 28 + Math.random() * 22; // 28-50ms — organic rhythm
  setTimeout(function() { typeText(el, text, idx + 1, callback); }, delay);
}

function startDots(el, base) {
  var count = 0;
  lastUpdateTime = Date.now();
  stopStaleBlink();

  dotsTimer = setInterval(function() {
    var elapsed = Date.now() - lastUpdateTime;

    if (elapsed > 3000) {
      // Stale — process stopped responding. Freeze dots, blink last one.
      clearInterval(dotsTimer);
      dotsTimer = null;
      startStaleBlink(el);
    } else {
      // Active — cycle dots normally
      count = (count % 3) + 1;
      el.textContent = base + '.'.repeat(count);
    }
  }, 380);
}

function startStaleBlink(el) {
  // Freeze text at current state, blink the last dot on/off
  var frozenText = el.textContent;
  var visible = true;
  staleTimer = setInterval(function() {
    visible = !visible;
    if (visible) {
      el.textContent = frozenText;
    } else {
      el.textContent = frozenText.slice(0, -1);
    }
  }, 600);
}

function stopStaleBlink() {
  if (staleTimer) {
    clearInterval(staleTimer);
    staleTimer = null;
  }
}

function stopDots() {
  if (dotsTimer) {
    clearInterval(dotsTimer);
    dotsTimer = null;
  }
  stopStaleBlink();
}

function updateLastStampText(text) {
  stopDots();
  lastUpdateTime = Date.now();
  if (currentTypingEl) {
    currentTypingEl.textContent = text;
    if (text.endsWith('...')) {
      startDots(currentTypingEl, text.slice(0, -3));
    }
  }
}

function fadeStamps() {
  stopDots();
  var stamps = stampArea.querySelectorAll('.stamp-line');
  stamps.forEach(function(s) {
    s.style.transition = 'opacity 0.3s ease';
    s.style.opacity = '0';
  });
}


// ═══════════════════════════════════════
//  READER
// ═══════════════════════════════════════

function populateReader(text, meta) {
  if (!text) return;

  // Store raw markdown for copy/export
  rawReaderMarkdown = text;

  // Set date stamp
  var now = new Date();
  var months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  var day = String(now.getDate()).padStart(2, '0');
  var month = months[now.getMonth()];
  var year = now.getFullYear();
  dateStamp.textContent = day + ' ' + month + ' ' + year;

  // Video metadata
  while (videoMeta.firstChild) {
    videoMeta.removeChild(videoMeta.firstChild);
  }
  if (meta && meta.title) {
    var titleEl = document.createElement('div');
    titleEl.className = 'meta-title';
    titleEl.textContent = meta.title;
    videoMeta.appendChild(titleEl);

    var details = [];
    if (meta.channel) details.push(meta.channel);
    if (meta.duration) details.push(meta.duration);
    if (meta.source) details.push(meta.source);
    if (details.length > 0) {
      var detailEl = document.createElement('div');
      detailEl.className = 'meta-detail';
      detailEl.textContent = details.join(' · ');
      videoMeta.appendChild(detailEl);
    }
  }

  // Clear
  while (readerArticle.firstChild) {
    readerArticle.removeChild(readerArticle.firstChild);
  }

  // Parse markdown → clean editorial HTML
  // Process line by line for precise control
  var lines = text.split('\n');
  var i = 0;

  while (i < lines.length) {
    var line = lines[i].trim();

    // Skip empty lines
    if (!line) { i++; continue; }

    // ── ## Section Header ──
    if (line.match(/^#{1,3}\s+/)) {
      var headerText = line.replace(/^#{1,3}\s+/, '').trim();
      var h = document.createElement('h4');
      h.className = 'section-header';
      h.textContent = headerText;
      readerArticle.appendChild(h);
      i++;
      continue;
    }

    // ── **Bold Title** body — insight format ──
    var boldMatch = line.match(/^\*\*(.+?)\*\*\s*(.*)/);
    if (boldMatch) {
      var div = document.createElement('div');
      div.className = 'insight';

      var title = document.createElement('span');
      title.className = 'insight-title';
      title.textContent = boldMatch[1];
      div.appendChild(title);

      // Collect body: rest of this line + continuation lines
      var bodyParts = [];
      if (boldMatch[2]) bodyParts.push(boldMatch[2]);
      // Continuation: next lines that aren't headers, insights, or empty
      while (i + 1 < lines.length) {
        var next = lines[i + 1].trim();
        if (!next || next.match(/^#{1,3}\s+/) || next.match(/^\*\*/) || next.match(/^[-*]\s+/) || next.match(/^\d+\.\s+/)) break;
        bodyParts.push(next);
        i++;
      }

      if (bodyParts.length > 0) {
        var body = document.createElement('span');
        body.className = 'insight-body';
        body.textContent = ' ' + bodyParts.join(' ');
        div.appendChild(body);
      }

      readerArticle.appendChild(div);
      i++;
      continue;
    }

    // ── Bullet / numbered list with bold — insight variant ──
    var listMatch = line.match(/^(?:[-*]|\d+\.)\s+\*\*(.+?)\*\*\s*(.*)/);
    if (listMatch) {
      var div2 = document.createElement('div');
      div2.className = 'insight';

      var title2 = document.createElement('span');
      title2.className = 'insight-title';
      title2.textContent = listMatch[1];
      div2.appendChild(title2);

      if (listMatch[2]) {
        var body2 = document.createElement('span');
        body2.className = 'insight-body';
        body2.textContent = ' ' + listMatch[2];
        div2.appendChild(body2);
      }

      readerArticle.appendChild(div2);
      i++;
      continue;
    }

    // ── Bullet / numbered list without bold ──
    var plainListMatch = line.match(/^(?:[-*]|\d+\.)\s+(.*)/);
    if (plainListMatch) {
      var p = document.createElement('p');
      p.textContent = renderInlineBold(plainListMatch[1]);
      readerArticle.appendChild(p);
      i++;
      continue;
    }

    // ── Regular paragraph — collect consecutive lines ──
    var paraParts = [line];
    while (i + 1 < lines.length) {
      var next2 = lines[i + 1].trim();
      if (!next2 || next2.match(/^#{1,3}\s+/) || next2.match(/^\*\*/) || next2.match(/^[-*]\s+/) || next2.match(/^\d+\.\s+/)) break;
      paraParts.push(next2);
      i++;
    }

    var p2 = document.createElement('p');
    var paraText = paraParts.join(' ');

    // Handle inline **bold** within paragraph
    if (paraText.indexOf('**') >= 0) {
      appendWithInlineBold(p2, paraText);
    } else {
      p2.textContent = paraText;
    }
    readerArticle.appendChild(p2);
    i++;
  }
}

// Helper: render inline **bold** within a text node
function appendWithInlineBold(parent, text) {
  var parts = text.split(/\*\*(.+?)\*\*/);
  for (var j = 0; j < parts.length; j++) {
    if (j % 2 === 0) {
      // Normal text
      if (parts[j]) parent.appendChild(document.createTextNode(parts[j]));
    } else {
      // Bold text
      var strong = document.createElement('strong');
      strong.textContent = parts[j];
      parent.appendChild(strong);
    }
  }
}

// Helper: strip **bold** markers for plain text use
function renderInlineBold(text) {
  return text.replace(/\*\*(.+?)\*\*/g, '$1');
}

// Reader actions
newBtn.addEventListener('click', function() {
  stopPipeline();
  urlInput.value = '';
  // Restore tagline
  var tagline = document.getElementById('brandTagline');
  if (tagline) tagline.classList.remove('hidden');
  // Clear stamps
  while (stampArea.firstChild) {
    stampArea.removeChild(stampArea.firstChild);
  }
  navigateTo('input');
});

copyBtn.addEventListener('click', function() {
  var text = getReaderText();
  if (!text) return;

  copyToClipboard(text).then(function() {
    showButtonSuccess(copyBtn, 'Copied!');
  });
});

function copyToClipboard(text) {
  // navigator.clipboard may not work in pywebview (non-HTTPS)
  if (navigator.clipboard && window.isSecureContext) {
    return navigator.clipboard.writeText(text);
  }
  // Fallback: hidden textarea trick
  var ta = document.createElement('textarea');
  ta.value = text;
  ta.style.position = 'fixed';
  ta.style.left = '-9999px';
  ta.style.opacity = '0';
  document.body.appendChild(ta);
  ta.select();
  document.execCommand('copy');
  document.body.removeChild(ta);
  return Promise.resolve();
}

exportBtn.addEventListener('click', function() {
  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.reveal_in_finder().then(function(result) {
      if (result && result.revealed) {
        showButtonSuccess(exportBtn, 'Opened');
      }
    }).catch(function() {});
  }
});

function getReaderText() {
  return rawReaderMarkdown || '';
}

function showButtonSuccess(btn, text) {
  var original = btn.textContent;
  btn.textContent = text;
  btn.classList.add('success');
  setTimeout(function() {
    btn.textContent = original;
    btn.classList.remove('success');
  }, 2000);
}


// ═══════════════════════════════════════
//  LIBRARY
// ═══════════════════════════════════════

var activeTab = 'fresh';
var libraryCache = [];

// Tab click handlers
document.querySelectorAll('.sidebar .tab').forEach(function(tab) {
  tab.addEventListener('click', function() {
    var bracket = this.getAttribute('data-bracket');
    if (bracket) {
      activeTab = bracket;
      updateTabStyles();
      loadLibrary();
    }
  });
});

function updateTabStyles() {
  document.querySelectorAll('.sidebar .tab').forEach(function(tab) {
    if (tab.getAttribute('data-bracket') === activeTab) {
      tab.classList.add('active');
    } else {
      tab.classList.remove('active');
    }
  });
}

function loadLibrary() {
  if (!window.pywebview || !window.pywebview.api) return;

  window.pywebview.api.get_library(activeTab).then(function(entries) {
    libraryCache = entries || [];
    renderLibrary(libraryCache);
  }).catch(function() {
    libraryCache = [];
    renderLibrary([]);
  });

  // Update tab counts
  window.pywebview.api.get_library_counts().then(function(counts) {
    if (!counts) return;
    document.querySelectorAll('.sidebar .tab').forEach(function(tab) {
      var bracket = tab.getAttribute('data-bracket');
      var count = counts[bracket] || 0;
      var span = tab.querySelector('span');
      var label = bracket.charAt(0).toUpperCase() + bracket.slice(1);
      span.textContent = count > 0 ? label + ' ' + count : label;
    });
  }).catch(function() {});
}

function renderLibrary(entries) {
  // Clear
  while (fileList.firstChild) {
    fileList.removeChild(fileList.firstChild);
  }

  // Filter by search
  var query = (searchBar.value || '').trim().toLowerCase();
  var filtered = entries;
  if (query) {
    filtered = entries.filter(function(e) {
      return e.title.toLowerCase().indexOf(query) >= 0;
    });
  }

  if (filtered.length === 0) {
    var empty = document.createElement('div');
    empty.className = 'library-empty';
    var emptyText = document.createElement('p');
    emptyText.textContent = query ? 'No matches.' : 'No entries yet.';
    empty.appendChild(emptyText);
    fileList.appendChild(empty);
    return;
  }

  filtered.forEach(function(entry) {
    var row = document.createElement('div');
    row.className = 'file-row';

    var title = document.createElement('span');
    title.className = 'file-title';
    title.textContent = entry.title;

    var date = document.createElement('span');
    date.className = 'file-date';
    date.textContent = entry.date_str;

    row.appendChild(title);
    if (entry.kind === 'transcript') {
      var badge = document.createElement('span');
      badge.className = 'file-badge';
      badge.textContent = 'T';
      row.appendChild(badge);
    }
    row.appendChild(date);

    row.addEventListener('click', function() {
      openEntry(entry);
    });

    fileList.appendChild(row);
  });
}

// Search filtering
searchBar.addEventListener('input', function() {
  renderLibrary(libraryCache);
});

function openEntry(entry) {
  if (!window.pywebview || !window.pywebview.api) return;

  window.pywebview.api.get_entry(entry.path).then(function(result) {
    if (result && result.content) {
      populateReader(result.content);
      // Set date from entry
      dateStamp.textContent = entry.date_str;
      navigateTo('reader');
    }
  }).catch(function() {});
}


// ═══════════════════════════════════════
//  SETTINGS
// ═══════════════════════════════════════

settingsTrigger.addEventListener('click', openSettings);
settingsDone.addEventListener('click', saveAndCloseSettings);

// Click backdrop to close (but not the panel itself)
settingsOverlay.addEventListener('click', function(e) {
  if (e.target === settingsOverlay) {
    saveAndCloseSettings();
  }
});

function openSettings() {
  settingsOverlay.classList.remove('hidden');

  // Load current settings from Python
  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.load_settings().then(function(s) {
      if (!s) return;
      apiKeyInput.value = s.api_key || '';
      langSelect.value = s.language || 'auto';
      modelSelect.value = s.model || 'turbo';
      contextInput.value = s.context || '';
      analysisPrompt.value = s.analysis_prompt || '';
      updateApiKeyStatus(s.api_key);
    }).catch(function() {});
  }
}

function closeSettings() {
  settingsOverlay.classList.add('hidden');
}

function saveAndCloseSettings() {
  var data = {
    api_key: apiKeyInput.value.trim(),
    language: langSelect.value,
    model: modelSelect.value,
    context: contextInput.value.trim(),
    analysis_prompt: analysisPrompt.value.trim(),
  };

  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.save_settings(data).then(function(result) {
      if (result && result.error) {
        apiKeyStatus.textContent = result.error;
        apiKeyStatus.className = 'settings-status error';
        return;  // Don't close if error
      }
      closeSettings();
    }).catch(function() {
      closeSettings();
    });
  } else {
    closeSettings();
  }
}

function updateApiKeyStatus(key) {
  if (!key) {
    apiKeyStatus.textContent = '';
    apiKeyStatus.className = 'settings-status';
  } else if (key.startsWith('sk-or-')) {
    apiKeyStatus.textContent = 'Saved';
    apiKeyStatus.className = 'settings-status ok';
  } else {
    apiKeyStatus.textContent = 'Must start with sk-or-';
    apiKeyStatus.className = 'settings-status error';
  }
}

apiKeyInput.addEventListener('input', function() {
  updateApiKeyStatus(this.value.trim());
});


// ═══════════════════════════════════════
//  INIT
// ═══════════════════════════════════════

// Wait for pywebview to be ready, then check if first run
function init() {
  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.has_api_key().then(function(hasKey) {
      if (!hasKey) {
        openSettings();
      }
    }).catch(function() {});
  }
}

// pywebview fires 'pywebviewready' when the bridge is available
if (window.pywebview) {
  init();
} else {
  window.addEventListener('pywebviewready', init);
}
