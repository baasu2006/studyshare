// ── Search filter ──────────────────────────────────────────────────────
const searchBar = document.getElementById('searchBar');
if (searchBar) {
    searchBar.addEventListener('input', function(e) {
        const term = e.target.value.toLowerCase().trim();
        document.querySelectorAll('.note-card').forEach(card => {
            card.style.display = (card.getAttribute('data-title') || '').includes(term) ? '' : 'none';
        });
    });
}

// ── Filter tabs ────────────────────────────────────────────────────────
function filterNotes(type, btn) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    btn.classList.add('active');
    document.querySelectorAll('.note-card').forEach(card => {
        if (type === 'all')    card.style.display = '';
        else if (type === 'pinned') card.style.display = card.getAttribute('data-pinned') === 'true' ? '' : 'none';
        else if (type === 'admin')  card.style.display = card.getAttribute('data-admin')  === 'true' ? '' : 'none';
    });
}

// ── Subject dropdown "Other" ───────────────────────────────────────────
function checkOther(sel) {
    const inp = document.getElementById('otherInput');
    if (!inp) return;
    inp.style.display = sel.value === 'Other' ? 'block' : 'none';
    inp.value === 'Other' ? inp.setAttribute('required','true') : inp.removeAttribute('required');
}

// ── File label update ─────────────────────────────────────────────────
function updateFileLabel(input) {
    const lbl = document.getElementById('fileLabel');
    if (lbl && input.files.length) lbl.textContent = input.files[0].name;
}

// ── Copy share link ───────────────────────────────────────────────────
function copyShareLink(noteId) {
    const url = `${BASE_URL}/share/${noteId}`;
    navigator.clipboard.writeText(url).then(() => showToast('Share link copied! 🔗'));
}

function showToast(msg) {
    const t = document.getElementById('toast');
    if (!t) return;
    t.textContent = msg;
    t.style.display = 'block';
    setTimeout(() => t.style.display = 'none', 3000);
}

// ── AI Explain ────────────────────────────────────────────────────────
function explainTopic() {
    const inp = document.getElementById('aiTopicInput');
    if (!inp || !inp.value.trim()) return;
    quickExplain(inp.value.trim());
}

function quickExplain(topic) {
    const modal   = document.getElementById('aiModal');
    const loading = document.getElementById('aiLoading');
    const content = document.getElementById('aiContent');
    const titleEl = document.getElementById('modalTopic');
    const textEl  = document.getElementById('aiExplanationText');
    const ytSec   = document.getElementById('ytSection');
    const ytCards = document.getElementById('ytCards');

    modal.style.display   = 'flex';
    loading.style.display = 'flex';
    content.style.display = 'none';
    titleEl.textContent   = topic;
    textEl.innerHTML      = '';
    ytCards.innerHTML     = '';
    ytSec.style.display   = 'none';

    fetch('/api/explain', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic })
    })
    .then(r => r.json())
    .then(data => {
        loading.style.display = 'none';
        content.style.display = 'block';

        const raw = data.explanation || 'No explanation available.';

        // Parse structured sections: SUMMARY: / KEY CONCEPTS: / REAL-WORLD EXAMPLE:
        const sections = [
            { key: 'SUMMARY',             icon: '📌', label: 'Summary' },
            { key: 'KEY CONCEPTS',        icon: '🔑', label: 'Key Concepts' },
            { key: 'REAL-WORLD EXAMPLE',  icon: '🌍', label: 'Real-World Example' },
        ];

        let html = '';
        let remaining = raw;
        let foundAny = false;

        sections.forEach((sec, i) => {
            const regex = new RegExp(sec.key + '\\s*:\\s*', 'i');
            const nextKeys = sections.slice(i + 1).map(s => s.key + '\\s*:').join('|');
            const endRegex = nextKeys ? new RegExp(nextKeys, 'i') : null;

            const startMatch = regex.exec(remaining);
            if (!startMatch) return;

            foundAny = true;
            let text = remaining.slice(startMatch.index + startMatch[0].length);
            if (endRegex) {
                const endMatch = endRegex.exec(text);
                if (endMatch) text = text.slice(0, endMatch.index);
            }
            text = text.trim();

            // Render bullet points (lines starting with •)
            const lines = text.split('\n').filter(l => l.trim());
            const rendered = lines.map(l => {
                const clean = l.trim().replace(/^•\s*/, '');
                return l.trim().startsWith('•')
                    ? `<li>${clean}</li>`
                    : `<p style="margin:0">${clean}</p>`;
            }).join('');
            const wrapped = rendered.includes('<li>') ? `<ul class="ai-bullets">${rendered}</ul>` : rendered;

            html += `
                <div class="explain-section">
                    <div class="explain-sec-header">
                        <span class="explain-sec-icon">${sec.icon}</span>
                        <span class="explain-sec-label">${sec.label}</span>
                    </div>
                    <div class="explain-sec-body">${wrapped}</div>
                </div>`;
        });

        // Fallback: plain text if no sections parsed
        if (!foundAny) {
            html = `<div class="explain-section"><div class="explain-sec-body"><p>${raw.replace(/\n/g,'<br>')}</p></div></div>`;
        }

        // Source badge
        const sourceMap = { claude: '⚡ Groq (Llama 3)', openai: '🤖 GPT-4o mini' };
        if (data.source && sourceMap[data.source]) {
            html = `<div class="ai-source-badge">${sourceMap[data.source]}</div>` + html;
        }

        textEl.innerHTML = html;

        // YouTube cards
        if (data.videos && data.videos.length) {
            ytSec.style.display = 'block';
            data.videos.forEach(v => {
                ytCards.innerHTML += `
                    <a href="${v.url}" target="_blank" class="yt-card">
                        <img src="${v.thumbnail}" alt="${v.title}" class="yt-thumb">
                        <div class="yt-info">
                            <p class="yt-title">${v.title}</p>
                            <p class="yt-channel">${v.channel}</p>
                        </div>
                    </a>`;
            });
        }
    })
    .catch(err => {
        loading.style.display = 'none';
        content.style.display = 'block';
        textEl.innerHTML = `<div class="explain-section"><div class="explain-sec-body"><p>⚠️ Could not connect to AI service.<br><small>${err}</small></p></div></div>`;
    });
}

function closeModal(e) {
    if (e.target.classList.contains('modal-overlay'))
        document.getElementById('aiModal').style.display = 'none';
}
