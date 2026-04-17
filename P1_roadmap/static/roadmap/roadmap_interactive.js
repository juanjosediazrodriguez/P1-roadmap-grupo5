'use strict';

// ─────────────────────────────────────────────────────────────────────────────
// 1. DATOS Y ESTADO
// ─────────────────────────────────────────────────────────────────────────────

const D = JSON.parse(document.getElementById('roadmap-data-json').textContent);
const STATE_KEY = 'careermap_roadmap_state';

let state = null;

function buildInitialState() {
    const semester_map = {};
    for (const [semNum, courseIds] of Object.entries(D.semester_map)) {
        semester_map[String(semNum)] = [...courseIds];
    }
    return {
        semester_map,
        selections: {
            nfi:       Object.fromEntries(D.nfi_umbrella_pks.map(pk => [String(pk), null])),
            electiva:  Object.fromEntries(D.electiva_mat_umbrella_pks.map(pk => [String(pk), null])),
            prof_track: { '207': null, '208': null },
            emphasis:   { '211': null },
        },
    };
}

// ─────────────────────────────────────────────────────────────────────────────
// 2. PERSISTENCIA
// ─────────────────────────────────────────────────────────────────────────────

function saveState() {
    try {
        // Guardar en servidor
        fetch('/roadmap/state/save/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            body: JSON.stringify(state),
        }).catch(err => console.warn('Error guardando estado:', err));
        // Guardar también en sessionStorage como caché local
        sessionStorage.setItem(STATE_KEY, JSON.stringify(state));
        updateAllRemoveBtns();
    } catch (e) {
        console.warn('No se pudo guardar el estado:', e);
    }
}

function loadState() {
    try {
        const raw = sessionStorage.getItem(STATE_KEY);
        if (!raw) return false;
        const saved = JSON.parse(raw);
        // Solo verificar que los semestres BASE coincidan, no los extras
        const currentSems = Object.keys(D.semester_map).map(String).sort();
        const savedBaseSems = currentSems.filter(s => 
            Object.keys(saved.semester_map || {}).includes(s)
        );
        if (savedBaseSems.length !== currentSems.length) return false;
        state = saved;
        return true;
    } catch (e) {
        return false;
    }
}

function initFromServer() {
    return fetch('/roadmap/state/load/')
        .then(function(res) { return res.json(); })
        .then(function(data) {
            if (data.ok && data.state && Object.keys(data.state).length > 0) {
                const currentSems = Object.keys(D.semester_map).map(String).sort();
                const savedSems = Object.keys(data.state.semester_map || {});
                // Verificar que todos los semestres BASE estén presentes
                const allBasePresent = currentSems.every(s => savedSems.includes(s));
                if (allBasePresent) {
                    state = data.state;
                    sessionStorage.setItem(STATE_KEY, JSON.stringify(state));
                    return true;
                }
            }
            return false;
        })
        .catch(function(e) {
            console.warn('No se pudo cargar estado del servidor:', e);
            return false;
        });
}

function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}

function resetState() {
    sessionStorage.removeItem(STATE_KEY);
    state = buildInitialState();
    rebuildAllSemesters();
    updateContextBar();
    validateAll();
    showToast('Roadmap reiniciado exitosamente', 'info');
}

// ─────────────────────────────────────────────────────────────────────────────
// 3. HELPERS
// ─────────────────────────────────────────────────────────────────────────────

function getCourse(id) {
    return D.course_map[String(id)] || null;
}

function getCategoryClass(category) {
    if (!category) return '';
    return 'category-' + category.toLowerCase().replace(/_/g, '');
}

function getCategoryColor(category) {
    const colors = {
        'BASIC_SCIENCE':      '#4a90e2',
        'BASIC_ENGINEERING':  '#20c997',
        'NFI':                '#fd7e14',
        'DISCIPLINARY':       '#dc3545',
        'PROFESSIONAL_TRACK': '#28a745',
        'FLEXIBLE_TRACK':     '#198754',
        'PRACTICE':           '#b91c1c',
        'EMPHASIS':           '#2ecc71',
        'SPECIALIZATION':     '#27ae60',
    };
    return colors[category] || '#27ae60';
}

function buildDetailSelectBtn(label, color, onClick) {
    const btn = document.createElement('button');
    btn.className = 'rm-detail-select-btn';
    btn.style.cssText = `
        position: absolute;
        top: 50%;
        right: 60px;
        transform: translateY(-50%);
        border-radius: 20px;
        font-size: 0.82rem;
        padding: 0.35rem 1.1rem;
        font-weight: 600;
        border: 1.5px solid ${color};
        background: transparent;
        color: ${color};
        cursor: pointer;
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
        transition: background 0.15s;
        white-space: nowrap;
        z-index: 10;
    `;
    btn.innerHTML = `<i class="fas fa-plus"></i> ${label}`;
    btn.addEventListener('mouseenter', () => {
        btn.style.background = `${color}22`;
    });
    btn.addEventListener('mouseleave', () => {
        btn.style.background = 'transparent';
    });
    btn.addEventListener('click', onClick);

    // Wrapper del header del modal para posicionarlo bien
    return btn;
}

function getSemesterOfCourse(courseId) {
    const id = String(courseId);
    for (const [sem, ids] of Object.entries(state.semester_map)) {
        if (ids.map(String).includes(id)) return parseInt(sem);
    }
    return null;
}

function removeCourseFromSemester(courseId, hintSem) {
    const id = courseId;
    if (hintSem) {
        const list = state.semester_map[String(hintSem)];
        if (list) {
            const idx = list.indexOf(id);
            if (idx !== -1) { list.splice(idx, 1); return; }
        }
    }
    for (const list of Object.values(state.semester_map)) {
        const idx = list.indexOf(id);
        if (idx !== -1) { list.splice(idx, 1); return; }
    }
}

function updateAllRemoveBtns() {
    Object.keys(state.semester_map).map(Number).filter(n => n > 9).forEach(semNum => {
        const col = getSemesterColumn(semNum);
        if (col) updateRemoveBtn(col, semNum);
    });
}

function getScrollElement() {
    // El que tiene overflow real es el que tiene scrollWidth > clientWidth
    const outer = document.querySelector('.roadmap-wrapper-outer');
    const inner = document.querySelector('.roadmap-wrapper');
    if (outer && outer.scrollWidth > outer.clientWidth) return outer;
    if (inner && inner.scrollWidth > inner.clientWidth) return inner;
    // Fallback: el que tenga overflow-x auto/scroll
    return outer || inner;
}

// ─────────────────────────────────────────────────────────────────────────────
// 4. RENDER DE TARJETAS
// ─────────────────────────────────────────────────────────────────────────────

function buildCourseCard(course, semNum, parentLabel) {
    const cat         = getCategoryClass(course.category);
    const prereqCount = (course.prerequisites || []).length;
    const coreqCount  = (course.corequisites  || []).length;
    const isUmbrella  = course.is_umbrella;
    const isFlexible  = D.flex_umbrella_pks.map(String).includes(String(course.id));

    const card = document.createElement('div');
    card.className = `course-card ${cat}`;
    card.dataset.courseId   = course.id;
    card.dataset.semNum     = semNum;
    card.dataset.isUmbrella = isUmbrella ? 'true' : 'false';
    card.dataset.isFlexible = isFlexible ? 'true' : 'false';
    card.style.cursor = 'pointer';

    if (isFlexible) {
        card.setAttribute('data-bs-toggle', 'modal');
        card.setAttribute('data-bs-target', `#courseModal${course.id}`);
    } else if (isUmbrella) {
        card.addEventListener('click', () => {
            const currentSemNum = parseInt(card.dataset.semNum);
            openSelectionModal(course, currentSemNum);
        });
        } else {
        card.setAttribute('data-bs-toggle', 'modal');
        card.setAttribute('data-bs-target', `#courseModal${course.id}`);
    }

    card.innerHTML = `
        <div class="course-card-header">
            <span class="course-code">${course.code || '—'}</span>
            <span class="course-credits">${course.credits} cr</span>
        </div>
        ${parentLabel ? `<div class="rm-parent-label">${parentLabel}</div>` : ''}
        <div class="course-name">${course.name}</div>
        ${isFlexible ? `<div class="rm-flexible-badge">
            <i class="fas fa-clock me-1"></i>Próximamente
        </div>` : ''}
        ${(!isFlexible && (prereqCount > 0 || coreqCount > 0)) ? `
        <div class="course-prereqs">
            ${prereqCount > 0 ? `<span class="prereq-dot"></span>${prereqCount} Pre` : ''}
            ${coreqCount  > 0 ? `<span class="coreq-dot" style="width:8px;height:8px;border-radius:50%;background-color:#9c27b0;flex-shrink:0;box-shadow:0 0 8px #9c27b0;margin-left:0.5rem;"></span>${coreqCount} Co` : ''}
        </div>` : ''}
        <div class="course-warnings"></div>
        ${(isUmbrella && !isFlexible) ? `<div class="rm-umbrella-hint">▾ elegir</div>` : ''}
    `;

    return card;
}

// ─────────────────────────────────────────────────────────────────────────────
// 5. RENDER DE SEMESTRES
// ─────────────────────────────────────────────────────────────────────────────

function getSemesterColumn(semNum) {
    return document.querySelector(`.semester-col[data-sem-num="${semNum}"]`);
}

function rebuildSemesterColumn(semNum) {
    const col = getSemesterColumn(semNum);
    if (!col) return;

    col.querySelectorAll('.course-card, .credit-warning').forEach(el => el.remove());

    const courseIds = state.semester_map[String(semNum)] || [];
    let totalCredits = 0;

    // Construir mapa inverso: courseId -> parentLabel
    const parentLabels = buildParentLabelMap();

    for (const id of courseIds) {
        const course = getCourse(id);
        if (!course) continue;
        totalCredits += course.credits;
        const parentLabel = parentLabels[String(id)] || null;
        col.appendChild(buildCourseCard(course, semNum, parentLabel));
    }

    const creditsEl = col.querySelector('.semester-credits');
    if (creditsEl) {
        creditsEl.textContent = `${totalCredits} créditos`;
        creditsEl.classList.toggle('over-limit', totalCredits > 21);
    }

    // Actualizar botón eliminar si es semestre extra
    if (semNum > 9) updateRemoveBtn(col, semNum);
}

function buildParentLabelMap() {
    const map = {};

    // NFI
    const nfiCodes = { '23': 'NFI3', '24': 'NFI4', '25': 'NFI5' };
    for (const [pk, selId] of Object.entries(state.selections.nfi)) {
        if (selId !== null) map[String(selId)] = nfiCodes[pk] || `NFI-${pk}`;
    }

    // Electivas
    const electCodes = { '26': 'ELECT-MAT1', '32': 'ELECT-MAT2' };
    for (const [pk, selId] of Object.entries(state.selections.electiva)) {
        if (selId !== null) map[String(selId)] = electCodes[pk] || `ELECT-${pk}`;
    }

    // Trayectorias profesionalizantes
    const profCodes = { '207': 'TRACK-PROF1', '208': 'TRACK-PROF2' };
    for (const [slotPk, trackUmbrellaPk] of Object.entries(state.selections.prof_track)) {
        if (trackUmbrellaPk === null) continue;
        const trackData = D.tracks[String(trackUmbrellaPk)];
        if (!trackData) continue;
        const label = profCodes[slotPk] || `PROF-${slotPk}`;
        for (const c of [...trackData.courses_sem6, ...trackData.courses_sem7]) {
            map[String(c.id)] = label;
        }
    }

    // Línea de énfasis
    const empUmbrellaPk = state.selections.emphasis['211'];
    if (empUmbrellaPk !== null) {
        const linePk   = D.emphasis_umbrella_to_line[String(empUmbrellaPk)];
        const lineData = linePk ? D.emphasis_lines[String(linePk)] : null;
        if (lineData) {
            for (const c of lineData.courses) {
                map[String(c.id)] = 'EMPHASIS-LINE';
            }
        }
    }

    return map;
}

function buildSemesterColumn(semNum) {
    const col = document.createElement('div');
    col.className = 'semester-col';
    col.dataset.semNum = semNum;

    col.innerHTML = `
        <div class="semester-circle">${semNum}</div>
        <div class="semester-title">Semestre ${semNum}</div>
        <div class="semester-credits">0 créditos</div>
        <button class="rm-remove-semester-btn" data-sem="${semNum}" title="Eliminar semestre" style="display:none;">
            <i class="fas fa-trash-can"></i>
        </button>
    `;

    col.querySelector('.rm-remove-semester-btn').addEventListener('click', () => removeSemester(semNum));
    return col;
}

function updateRemoveBtn(col, semNum) {
    const btn = col.querySelector('.rm-remove-semester-btn');
    if (!btn) return;
    const isEmpty = (state.semester_map[String(semNum)] || []).length === 0;
    btn.style.display = isEmpty ? 'flex' : 'none';
}

function rebuildAllSemesters() {
    const track = document.querySelector('.roadmap-track');
    // Limpiar botón + si quedó dentro del track por error
    track.querySelector('.rm-add-semester-col')?.remove();
    if (!track) return;

    // Para semestres existentes (del template): solo limpiar tarjetas
    for (const semNum of Object.keys(state.semester_map).map(Number).sort((a, b) => a - b)) {
        let col = getSemesterColumn(semNum);
        
        if (!col) {
            // Semestre nuevo (> 9): crear columna completa
            col = buildSemesterColumn(semNum);
            // Insertar antes del botón +, o al final si no existe
            const addCol = track.querySelector('.rm-add-semester-col');
            if (addCol) track.insertBefore(col, addCol);
            else track.appendChild(col);
        } else {
            // Semestre existente: solo actualizar botón eliminar si aplica
            if (semNum > 9) updateRemoveBtn(col, semNum);
        }

        // Rellenar tarjetas en todos los casos
        rebuildSemesterColumn(semNum);
    }

    // Eliminar columnas extra que ya no están en el estado
    track.querySelectorAll('.semester-col').forEach(col => {
        const semNum = parseInt(col.dataset.semNum);
        if (!state.semester_map[String(semNum)]) {
            col.remove();
        }
    });

    // Botón + fuera del track — crearlo si no existe
    if (!document.querySelector('.rm-add-semester-col')) {
        let addCol = document.querySelector('.rm-add-semester-col');
        if (!addCol) {
            addCol = document.createElement('div');
            addCol.className = 'rm-add-semester-col';
            addCol.innerHTML = `
                <button class="rm-add-semester-btn" title="Agregar semestre">
                    <i class="fas fa-plus"></i>
                </button>
                <span class="rm-add-semester-label">Agregar<br>semestre</span>
            `;
            addCol.querySelector('.rm-add-semester-btn').addEventListener('click', addSemester);
        }
        // Siempre asegurar que esté al final del track
        track.appendChild(addCol);
    }

    initSortable();
}

function getMaxSemester() {
    return Math.max(...Object.keys(state.semester_map).map(Number));
}

function addSemester() {
    const newSem = getMaxSemester() + 1;
    state.semester_map[String(newSem)] = [];
    saveState();
    rebuildAllSemesters();
    validateAll();
    // Scrollear hasta el final para mostrar el nuevo semestre
    const outer = document.querySelector('.roadmap-wrapper-outer') ||
                  document.querySelector('.roadmap-wrapper');
    if (outer) setTimeout(() => { outer.scrollLeft = outer.scrollWidth; }, 50);
}

function removeSemester(semNum) {
    if (semNum <= 9) return; // Nunca eliminar los primeros 9
    const list = state.semester_map[String(semNum)];
    if (!list || list.length > 0) return; // Solo eliminar si está vacío
    delete state.semester_map[String(semNum)];
    saveState();
    rebuildAllSemesters();
    validateAll();
}

// ─────────────────────────────────────────────────────────────────────────────
// 6. VALIDACIÓN
// ─────────────────────────────────────────────────────────────────────────────

function validateAll() {
    // Limpiar warnings previos
    document.querySelectorAll('.prereq-warning, .coreq-warning').forEach(el => el.remove());
    document.querySelectorAll('.credit-warning').forEach(el => el.remove());
    document.querySelectorAll('.semester-credits.over-limit').forEach(el => {
        el.classList.remove('over-limit');
    });

    for (const [semStr, courseIds] of Object.entries(state.semester_map)) {
        const semNum = parseInt(semStr);
        let totalCredits = 0;

        for (const courseId of courseIds) {
            const course = getCourse(courseId);
            if (!course) continue;
            totalCredits += course.credits;

            const card = document.querySelector(`.course-card[data-course-id="${courseId}"]`);
            if (!card) continue;

            const warningsContainer = card.querySelector('.course-warnings');
            if (!warningsContainer) continue;
            warningsContainer.innerHTML = '';

            // Verificar prerrequisitos
            for (const prereq of (course.prerequisites || [])) {
                const prereqSem = getSemesterOfCourse(prereq.id);
                if (prereqSem === null || prereqSem >= semNum) {
                    const w = document.createElement('div');
                    w.className = 'prereq-warning';
                    w.innerHTML = `<i class="fas fa-exclamation-circle"></i> Pre: ${prereq.code || prereq.name} debe estar antes`;
                    warningsContainer.appendChild(w);
                }
            }

            // Verificar correquisitos
            for (const coreq of (course.corequisites || [])) {
                const coreqSem = getSemesterOfCourse(coreq.id);
                if (coreqSem === null || coreqSem !== semNum) {
                    const w = document.createElement('div');
                    w.className = 'coreq-warning';
                    w.innerHTML = `<i class="fas fa-link"></i> Co: ${coreq.code || coreq.name} debe estar en este semestre`;
                    warningsContainer.appendChild(w);
                }
            }
        }

        // Verificar límite de créditos
        const col = getSemesterColumn(semNum);
        if (!col) continue;

        const creditsEl = col.querySelector('.semester-credits');
        if (creditsEl) {
            creditsEl.textContent = `${totalCredits} créditos`;
            if (totalCredits > 21) {
                creditsEl.classList.add('over-limit');
                const creditWarn = document.createElement('div');
                creditWarn.className = 'credit-warning';
                creditWarn.innerHTML = `<i class="fas fa-exclamation-triangle"></i> Máximo de créditos: 21 (actual: ${totalCredits})`;
                const firstCard = col.querySelector('.course-card');
                if (firstCard) col.insertBefore(creditWarn, firstCard);
                else col.appendChild(creditWarn);
            }
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// 7. DRAG & DROP
// ─────────────────────────────────────────────────────────────────────────────

function showToast(message, type = 'info') {
    const existing = document.getElementById('rm-toast');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.id = 'rm-toast';
    const colors = {
        warning: { bg: '#7c3a10', border: '#f97316', color: '#fdba74' },
        info:    { bg: '#1a3a5c', border: '#4a90e2', color: '#93c5fd' },
        error:   { bg: '#5c1a1a', border: '#ef4444', color: '#fca5a5' },
    };
    const c = colors[type] || colors.info;
    toast.style.cssText = `
        position: fixed;
        bottom: 2rem;
        left: 50%;
        transform: translateX(-50%);
        background: ${c.bg};
        border: 1px solid ${c.border};
        border-radius: 10px;
        color: ${c.color};
        padding: 0.75rem 1.5rem;
        font-size: 0.85rem;
        font-weight: 500;
        z-index: 9999;
        white-space: nowrap;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        transition: opacity 0.3s ease;
    `;
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function initSortable() {
    // PKs de paraguas que NO se pueden mover de semestre
    const BLOCKED_UMBRELLA_PKS = new Set(['207', '208', '211']);

    document.querySelectorAll('.semester-col').forEach(col => {
        const semNum = parseInt(col.dataset.semNum);
        if (!semNum) return;

        if (col._sortable) col._sortable.destroy();

        col._sortable = Sortable.create(col, {
            group:       'roadmap',
            animation:   180,
            ghostClass:  'course-card--ghost',
            chosenClass: 'course-card--chosen',
            dragClass:   'course-card--drag',
            draggable:   '.course-card',
            filter:      '.rm-add-semester-col, .rm-add-semester-btn, .rm-add-semester-label',
            onStart() {
                document.querySelector('.roadmap-track')?.classList.add('rm-dragging');
            },
            onEnd(evt) {
                document.querySelector('.roadmap-track')?.classList.remove('rm-dragging');

                const courseId  = parseInt(evt.item.dataset.courseId);
                const fromCol   = evt.from.closest('.semester-col');
                const toCol     = evt.to.closest('.semester-col');
                const fromSem   = parseInt(fromCol.dataset.semNum);
                const toSem     = parseInt(toCol.dataset.semNum);
                // Calcular índice real contando solo course-cards
                const allCards = [...toCol.querySelectorAll('.course-card')];
                const newIndex = allCards.indexOf(evt.item);

                // Bloquear movimiento de paraguas de trayectoria, flexible y énfasis
                if (fromSem !== toSem && BLOCKED_UMBRELLA_PKS.has(String(courseId))) {
                    // Calcular posición real entre course-cards únicamente
                    const fromCards = [...fromCol.querySelectorAll('.course-card')];
                    const originalIdx = state.semester_map[String(fromSem)].indexOf(courseId);
                    const refCard = fromCards[originalIdx] || null;
                    if (refCard) {
                        fromCol.insertBefore(evt.item, refCard);
                    } else {
                        fromCol.appendChild(evt.item);
                    }
                    evt.item.dataset.semNum = fromSem;
                    showToast('Primero selecciona la trayectoria o línea de énfasis antes de moverla', 'warning');
                    return;
                }

                if (fromSem === toSem) {
                    const newOrder = [...toCol.querySelectorAll('.course-card')]
                        .map(c => parseInt(c.dataset.courseId));
                    state.semester_map[String(toSem)] = newOrder;
                    saveState();
                    validateAll();
                } else {
                    const fromList = state.semester_map[String(fromSem)];
                    const toList   = state.semester_map[String(toSem)];

                    const idx = fromList.indexOf(courseId);
                    if (idx !== -1) fromList.splice(idx, 1);

                    toList.splice(newIndex, 0, courseId);

                    evt.item.dataset.semNum = toSem;

                    saveState();
                    rebuildSemesterColumn(fromSem);
                    updateSemesterCredits(toSem);
                    validateAll();
                    initSortable();
                }
            },
        });
    });
}

function updateSemesterCredits(semNum) {
    const col = getSemesterColumn(semNum);
    if (!col) return;
    const courseIds = state.semester_map[String(semNum)] || [];
    let totalCredits = 0;
    for (const id of courseIds) {
        const course = getCourse(id);
        if (course) totalCredits += course.credits;
    }
    const creditsEl = col.querySelector('.semester-credits');
    if (creditsEl) {
        creditsEl.textContent = `${totalCredits} créditos`;
        creditsEl.classList.toggle('over-limit', totalCredits > 21);
    }
}

function reorderWithinSemester(semNum) {
    const col = getSemesterColumn(semNum);
    if (!col) return;
    const newOrder = [...col.querySelectorAll('.course-card')].map(c => parseInt(c.dataset.courseId));
    state.semester_map[String(semNum)] = newOrder;
    saveState();
    validateAll();
}

function moveCourse(courseId, fromSem, toSem, toIndex) {
    const fromList = state.semester_map[String(fromSem)];
    const toList   = state.semester_map[String(toSem)];
    if (!fromList || !toList) return;

    const idx = fromList.indexOf(courseId);
    if (idx === -1) return;
    fromList.splice(idx, 1);

    // Insertar en la posición correcta
    if (toIndex !== undefined && toIndex >= 0 && toIndex <= toList.length) {
        toList.splice(toIndex, 0, courseId);
    } else {
        toList.push(courseId);
    }

    saveState();
    rebuildSemesterColumn(fromSem);
    rebuildSemesterColumn(toSem);
    validateAll();
    initSortable();
}

// ─────────────────────────────────────────────────────────────────────────────
// 8. MODAL DE SELECCIÓN (compartido)
// ─────────────────────────────────────────────────────────────────────────────

let activeSelectionModal = null;

function createSelectionModalDOM() {
    if (document.getElementById('rm-selection-modal')) return;

    const div = document.createElement('div');
    div.innerHTML = `
    <div class="modal fade" id="rm-selection-modal" tabindex="-1" aria-hidden="true">
        <div class="modal-dialog modal-lg modal-dialog-centered modal-dialog-scrollable">
            <div class="modal-content" style="background:#1a1d27;border:1px solid #2a2d3a;border-radius:12px;">
                <div class="modal-body" style="background:#1a1d27;color:#fff;padding:2rem;padding-top:3rem;position:relative;">
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Cerrar"></button>
                    <h2 class="rm-sel-title mb-2" id="rm-sel-title"></h2>
                    <p class="text-secondary mb-4" id="rm-sel-note" style="font-size:0.9rem;"></p>
                    <div id="rm-sel-body" class="rm-sel-body"></div>
                </div>
            </div>
        </div>
    </div>

    <!-- Modal de confirmación para resetear el roadmap -->
    <div class="modal fade" id="rm-confirm-modal" tabindex="-1" aria-hidden="true">
        <div class="modal-dialog modal-dialog-centered" style="max-width:420px;">
            <div class="modal-content" style="background:#1a1d27;border:1px solid #2a2d3a;border-radius:12px;border-left:6px solid #ef4444 !important;">
                <div class="modal-body" style="background:#1a1d27;color:#fff;padding:2rem;text-align:center;">
                    <i class="fas fa-rotate-left" style="font-size:2.5rem;color:#ef4444;margin-bottom:1rem;display:block;"></i>
                    <h5 style="color:#fff;margin-bottom:0.5rem;">¿Reiniciar el roadmap?</h5>
                    <p style="color:#8f9bb3;font-size:0.9rem;margin-bottom:1.5rem;">
                        Perderás todas las selecciones de trayectorias, electivas, líneas de énfasis y los movimientos de cursos.
                    </p>
                    <div style="display:flex;gap:0.75rem;justify-content:center;">
                        <button class="btn btn-outline-light btn-sm" data-bs-dismiss="modal" style="border-radius:20px;padding:0.4rem 1.2rem;">
                            Cancelar
                        </button>
                        <button class="btn btn-danger btn-sm" id="rm-confirm-reset-btn" style="border-radius:20px;padding:0.4rem 1.2rem;">
                            Sí, reiniciar
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>`;

    document.body.appendChild(div.children[0]);
    document.body.appendChild(div.children[0]);

    document.getElementById('rm-confirm-reset-btn').addEventListener('click', () => {
        bootstrap.Modal.getInstance(document.getElementById('rm-confirm-modal')).hide();
        resetState();
    });
}

function showSelectionModal(category) {
    const modalEl     = document.getElementById('rm-selection-modal');
    const contentEl   = modalEl.querySelector('.modal-content');

    // Limpiar clases de categoría anteriores
    contentEl.className = contentEl.className
        .replace(/modal-category-\S+/g, '').trim();

    // Aplicar la categoría correcta
    if (category) {
        contentEl.classList.add(`modal-category-${category.toLowerCase().replace(/_/g, '')}`);
    }

    activeSelectionModal = bootstrap.Modal.getOrCreateInstance(modalEl);
    activeSelectionModal.show();
}

function closeSelectionModal() {
    if (activeSelectionModal) {
        activeSelectionModal.hide();
        activeSelectionModal = null;
    }
}

function openSelectionModal(course, semNum) {
    const pk = String(course.id);

    if (D.nfi_umbrella_pks.map(String).includes(pk)) {
        openNFIElectivaModal(course, semNum, 'nfi');
    } else if (D.electiva_mat_umbrella_pks.map(String).includes(pk)) {
        openNFIElectivaModal(course, semNum, 'electiva');
    } else if (pk === '207' || pk === '208') {
        openProfTrackModal(course, semNum, pk);
    } else if (pk === '211') {
        openEmphasisModal(course, semNum);
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// 9. SELECCIÓN NFI / ELECTIVAS
// ─────────────────────────────────────────────────────────────────────────────

function openNFIElectivaModal(course, semNum, type) {
    const pk      = String(course.id);
    const options = D.umbrella_options[pk] || [];
    const current = state.selections[type][pk];

    const usedIds = new Set();
    for (const [otherPk, selectedId] of Object.entries(state.selections[type])) {
        if (otherPk !== pk && selectedId !== null) usedIds.add(String(selectedId));
    }

    document.getElementById('rm-sel-title').textContent = course.name;
    document.getElementById('rm-sel-note').textContent  = type === 'nfi'
        ? 'Elige un curso de formación institucional. Haz click en uno para ver sus detalles y seleccionarlo.'
        : 'Elige una electiva de matemáticas. Haz click en uno para ver sus detalles y seleccionarlo.';

    const body = document.getElementById('rm-sel-body');
    body.innerHTML = '';

    for (const opt of options) {
        const isUsed     = usedIds.has(String(opt.id));
        const isSelected = String(opt.id) === String(current);

        const card = document.createElement('div');
        card.className = `rm-option-card ${getCategoryClass(opt.category)}
            ${isSelected ? 'rm-option-selected' : ''}
            ${isUsed     ? 'rm-option-disabled'  : ''}`;

        const prereqCount = (opt.prerequisites || []).length;
        const coreqCount  = (opt.corequisites  || []).length;

        card.innerHTML = `
            <div class="rm-option-header">
                <span class="option-code-badge">${opt.code || '—'}</span>
                <span class="option-credits-badge">${opt.credits} cr</span>
            </div>
            <div class="option-name">${opt.name}</div>
            ${prereqCount > 0 || coreqCount > 0 ? `
            <div class="course-prereqs" style="margin-top:0.4rem;">
                ${prereqCount > 0 ? `<span class="prereq-dot"></span>${prereqCount} Pre` : ''}
                ${coreqCount  > 0 ? `<span class="coreq-dot" style="width:8px;height:8px;border-radius:50%;background-color:#9c27b0;flex-shrink:0;box-shadow:0 0 8px #9c27b0;margin-left:0.5rem;"></span>${coreqCount} Co` : ''}
            </div>` : ''}
            ${isSelected ? '<div class="rm-option-badge-current"><i class="fas fa-check me-1"></i>Seleccionado</div>' : ''}
            ${isUsed     ? '<div class="rm-option-badge-used"><i class="fas fa-ban me-1"></i>Ya elegido en otro slot</div>' : ''}
            ${!isUsed ? `<button class="rm-select-btn ${isSelected ? 'rm-select-btn--active' : ''}" data-opt-id="${opt.id}">
                ${isSelected ? '<i class="fas fa-check me-1"></i>Seleccionado' : '<i class="fas fa-plus me-1"></i>Seleccionar'}
            </button>` : ''}
        `;

        // Click en la card: abrir modal de detalle del curso
        if (!isUsed) {
            card.style.cursor = 'pointer';
            card.addEventListener('click', (e) => {
                // Si el click fue en el botón seleccionar, no abrir modal de detalle
                if (e.target.closest('.rm-select-btn')) return;
                openCourseDetailFromSelection(opt, pk, semNum, type, course.name);
            });

            const selectBtn = card.querySelector('.rm-select-btn');
            if (selectBtn) {
                selectBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    confirmNFIElectivaSelection(pk, opt, semNum, type);
                    closeSelectionModal();
                });
            }
        }

        body.appendChild(card);
    }

    showSelectionModal(type === 'nfi' ? 'nfi' : 'basicscience');
}

function openCourseDetailFromSelection(course, umbrellaPk, semNum, type, umbrellaName) {
    closeSelectionModal();
    const modalEl = document.getElementById(`courseModal${course.id}`);
    if (!modalEl) return;

    // Limpiar botón anterior si existe
    modalEl.querySelector('.rm-detail-select-btn')?.remove();

    const color  = getCategoryColor(course.category);
    const header = modalEl.querySelector('.modal-body > .d-flex');
    if (header) {
        header.style.position = 'relative';
        const btn = buildDetailSelectBtn('Seleccionar', color, () => {
            bootstrap.Modal.getInstance(modalEl).hide();
            confirmNFIElectivaSelection(umbrellaPk, course, semNum, type);
            setTimeout(() => {
                openNFIElectivaModal(
                    { id: parseInt(umbrellaPk), name: umbrellaName },
                    semNum, type
                );
            }, 350);
        });
        header.appendChild(btn);
    }

    bootstrap.Modal.getOrCreateInstance(modalEl).show();
}

function confirmNFIElectivaSelection(umbrellaPk, selectedCourse, semNum, type) {
    
    const umbrellaIntId = parseInt(umbrellaPk);
    const previousId = state.selections[type][umbrellaPk];

    let realSemNum, targetId;
    if (previousId !== null) {
        realSemNum = getSemesterOfCourse(previousId);
        targetId   = previousId;
    } else {
        realSemNum = getSemesterOfCourse(umbrellaIntId);
        targetId   = umbrellaIntId;
    }
    if (realSemNum === null) realSemNum = semNum;

    const semList = state.semester_map[String(realSemNum)];
    if (!semList) return;

    const insertIdx = semList.indexOf(targetId);
    
    removeCourseFromSemester(targetId, realSemNum);

    if (!D.course_map[String(selectedCourse.id)]) {
        D.course_map[String(selectedCourse.id)] = selectedCourse;
    }

    if (insertIdx !== -1) {
        semList.splice(insertIdx, 0, selectedCourse.id);
    } else {
        semList.push(selectedCourse.id);
    }

    state.selections[type][umbrellaPk] = selectedCourse.id;

    saveState();
    rebuildSemesterColumn(realSemNum);
    if (realSemNum !== semNum) rebuildSemesterColumn(semNum);
    validateAll();
    initSortable();
    updateContextBar();
}

// ─────────────────────────────────────────────────────────────────────────────
// 10. SELECCIÓN TRAYECTORIAS PROFESIONALIZANTES
// ─────────────────────────────────────────────────────────────────────────────

function openProfTrackModal(course, semNum, slotPk) {
    const options       = D.prof_umbrella_options[slotPk] || [];
    const current       = state.selections.prof_track[slotPk];
    const otherSlotPk   = slotPk === '207' ? '208' : '207';
    const otherSelected = state.selections.prof_track[otherSlotPk];

    const slotLabel = slotPk === '207' ? 'Slot 1' : 'Slot 2';
    document.getElementById('rm-sel-title').textContent = `Trayectoria Profesionalizante — ${slotLabel}`;
    document.getElementById('rm-sel-note').textContent  =
        'Haz click en una trayectoria para ver sus cursos y seleccionarla. No puedes elegir la misma trayectoria en ambos slots.';

    const body = document.getElementById('rm-sel-body');
    body.innerHTML = '';

    for (const opt of options) {
        const isUsedByOther = String(opt.id) === String(otherSelected);
        const isSelected    = String(opt.id) === String(current);
        const trackData     = D.tracks[String(opt.id)];

        const card = document.createElement('div');
        card.className = `rm-option-card category-professionaltrack
            ${isSelected    ? 'rm-option-selected' : ''}
            ${isUsedByOther ? 'rm-option-disabled'  : ''}`;

        card.innerHTML = `
            <div class="rm-option-header">
                <span class="option-code-badge">${opt.code || '—'}</span>
                <span class="option-credits-badge">${opt.credits} cr</span>
            </div>
            <div class="option-name">${opt.name}</div>
            ${trackData ? `
            <div class="rm-track-preview">
                <div class="rm-track-sem">
                    <span class="rm-track-sem-label">Sem 6</span>
                    ${trackData.courses_sem6.map(c => `<span class="rm-track-course-chip">${c.code || c.name}</span>`).join('')}
                </div>
                <div class="rm-track-sem">
                    <span class="rm-track-sem-label">Sem 7</span>
                    ${trackData.courses_sem7.map(c => `<span class="rm-track-course-chip">${c.code || c.name}</span>`).join('')}
                </div>
            </div>` : ''}
            ${isSelected    ? '<div class="rm-option-badge-current"><i class="fas fa-check me-1"></i>Seleccionada</div>' : ''}
            ${isUsedByOther ? '<div class="rm-option-badge-used"><i class="fas fa-ban me-1"></i>Elegida en el otro slot</div>' : ''}
            ${!isUsedByOther ? `<button class="rm-select-btn ${isSelected ? 'rm-select-btn--active' : ''}" data-opt-id="${opt.id}">
                ${isSelected ? '<i class="fas fa-check me-1"></i>Seleccionada' : '<i class="fas fa-plus me-1"></i>Seleccionar trayectoria'}
            </button>` : ''}
        `;

        if (!isUsedByOther) {
            card.style.cursor = 'pointer';
            card.addEventListener('click', (e) => {
                if (e.target.closest('.rm-select-btn')) return;
                openTrackDetailFromSelection(opt, slotPk);
            });

            const selectBtn = card.querySelector('.rm-select-btn');
            if (selectBtn) {
                selectBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    confirmProfTrackSelection(slotPk, opt);
                    closeSelectionModal();
                });
            }
        }

        body.appendChild(card);
    }

    showSelectionModal('professionaltrack');
}

function openTrackDetailFromSelection(trackUmbrella, slotPk) {
    closeSelectionModal();
    const modalEl = document.getElementById(`courseModal${trackUmbrella.id}`);
    if (!modalEl) return;

    modalEl.querySelector('.rm-detail-select-btn')?.remove();

    const color  = getCategoryColor('PROFESSIONAL_TRACK');
    const header = modalEl.querySelector('.modal-body > .d-flex');
    if (header) {
        header.style.position = 'relative';
        const btn = buildDetailSelectBtn('Seleccionar trayectoria', color, () => {
            bootstrap.Modal.getInstance(modalEl).hide();
            confirmProfTrackSelection(slotPk, trackUmbrella);
        });
        header.appendChild(btn);
    }

    bootstrap.Modal.getOrCreateInstance(modalEl).show();
}

function confirmProfTrackSelection(slotPk, selectedTrackUmbrella) {
    const previousTrackPk = state.selections.prof_track[slotPk];

    if (previousTrackPk !== null) {
        // Quitar cursos de la trayectoria anterior de este slot
        removeProfTrackCourses(String(previousTrackPk));
    } else {
        // Primera vez: quitar la tarjeta paraguas (207 o 208)
        removeCourseFromSemester(parseInt(slotPk), null);
    }

    // Agregar cursos de la nueva trayectoria
    const trackData = D.tracks[String(selectedTrackUmbrella.id)];
    if (!trackData) return;

    const sem6List = state.semester_map['6'];
    const sem7List = state.semester_map['7'];

    for (const course of trackData.courses_sem6) {
        D.course_map[String(course.id)] = course;
        if (sem6List && !sem6List.includes(course.id)) sem6List.push(course.id);
    }
    for (const course of trackData.courses_sem7) {
        D.course_map[String(course.id)] = course;
        if (sem7List && !sem7List.includes(course.id)) sem7List.push(course.id);
    }

    state.selections.prof_track[slotPk] = selectedTrackUmbrella.id;

    saveState();
    rebuildSemesterColumn(6);
    rebuildSemesterColumn(7);
    validateAll();
    initSortable();
    updateContextBar();
}

function removeProfTrackCourses(trackUmbrellaPk) {
    const trackData = D.tracks[String(trackUmbrellaPk)];
    if (!trackData) return;
    const idsToRemove = new Set([
        ...trackData.courses_sem6.map(c => c.id),
        ...trackData.courses_sem7.map(c => c.id),
    ]);
    for (const semStr of Object.keys(state.semester_map)) {
        state.semester_map[semStr] = state.semester_map[semStr].filter(id => !idsToRemove.has(id));
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// 11. SELECCIÓN LÍNEA DE ÉNFASIS
// ─────────────────────────────────────────────────────────────────────────────

function openEmphasisModal(course, semNum) {
    const options = D.emphasis_umbrella_options['211'] || [];
    const current = state.selections.emphasis['211'];

    document.getElementById('rm-sel-title').textContent = 'Línea de Énfasis';
    document.getElementById('rm-sel-note').textContent  =
        'Haz click en una línea para ver sus cursos y seleccionarla.';

    const body = document.getElementById('rm-sel-body');
    body.innerHTML = '';

    for (const opt of options) {
        const linePk     = D.emphasis_umbrella_to_line[String(opt.id)];
        const lineData   = linePk ? D.emphasis_lines[String(linePk)] : null;
        const isSelected = String(opt.id) === String(current);

        const card = document.createElement('div');
        card.className = `rm-option-card category-emphasis ${isSelected ? 'rm-option-selected' : ''}`;
        card.style.cursor = 'pointer';

        card.innerHTML = `
            <div class="rm-option-header">
                <span class="option-code-badge">${opt.code || '—'}</span>
                <span class="option-credits-badge">${opt.credits} cr</span>
            </div>
            <div class="option-name">${opt.name}</div>
            ${lineData ? `
            <div class="rm-track-preview">
                <div class="rm-track-sem">
                    <span class="rm-track-sem-label">Cursos</span>
                    ${lineData.courses.map(c => `<span class="rm-track-course-chip">${c.code || c.name.substring(0,20)}</span>`).join('')}
                </div>
            </div>` : ''}
            ${isSelected ? '<div class="rm-option-badge-current"><i class="fas fa-check me-1"></i>Seleccionada</div>' : ''}
            <button class="rm-select-btn ${isSelected ? 'rm-select-btn--active' : ''}" data-opt-id="${opt.id}">
                ${isSelected ? '<i class="fas fa-check me-1"></i>Seleccionada' : '<i class="fas fa-plus me-1"></i>Seleccionar línea'}
            </button>
        `;

        card.addEventListener('click', (e) => {
            if (e.target.closest('.rm-select-btn')) return;
            openEmphasisDetailFromSelection(opt, linePk, lineData, semNum);
        });

        const selectBtn = card.querySelector('.rm-select-btn');
        if (selectBtn && linePk && lineData) {
            selectBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                confirmEmphasisSelection(opt, linePk, lineData, semNum);
                closeSelectionModal();
            });
        }

        body.appendChild(card);
    }

    showSelectionModal('emphasis');
}

function openEmphasisDetailFromSelection(emphasisUmbrella, linePk, lineData, semNum) {
    closeSelectionModal();
    const modalEl = document.getElementById(`courseModal${emphasisUmbrella.id}`);
    if (!modalEl) return;

    modalEl.querySelector('.rm-detail-select-btn')?.remove();

    const color  = getCategoryColor('EMPHASIS');
    const header = modalEl.querySelector('.modal-body > .d-flex');
    if (header) {
        header.style.position = 'relative';
        const btn = buildDetailSelectBtn('Seleccionar línea', color, () => {
            bootstrap.Modal.getInstance(modalEl).hide();
            if (linePk && lineData) confirmEmphasisSelection(emphasisUmbrella, linePk, lineData, semNum);
        });
        header.appendChild(btn);
    }

    bootstrap.Modal.getOrCreateInstance(modalEl).show();
}

function confirmEmphasisSelection(selectedUmbrella, linePk, lineData, semNum) {
    const previousUmbrellaPk = state.selections.emphasis['211'];

    if (previousUmbrellaPk !== null) {
        // Quitar cursos de la línea anterior
        const prevLinePk   = D.emphasis_umbrella_to_line[String(previousUmbrellaPk)];
        const prevLineData = prevLinePk ? D.emphasis_lines[String(prevLinePk)] : null;
        if (prevLineData) {
            const idsToRemove = new Set(prevLineData.courses.map(c => c.id));
            for (const semStr of Object.keys(state.semester_map)) {
                state.semester_map[semStr] = state.semester_map[semStr].filter(id => !idsToRemove.has(id));
            }
        }
    } else {
        // Primera vez: quitar el paraguas 211
        removeCourseFromSemester(211, semNum);
    }

    // Agregar cursos de la nueva línea al semestre 9
    if (!state.semester_map['9']) state.semester_map['9'] = [];

    for (const course of lineData.courses) {
        D.course_map[String(course.id)] = course;
        if (!state.semester_map['9'].includes(course.id)) {
            state.semester_map['9'].push(course.id);
        }
    }

    state.selections.emphasis['211'] = selectedUmbrella.id;

    saveState();
    rebuildSemesterColumn(9);
    validateAll();
    initSortable();
    updateContextBar();
}

// ─────────────────────────────────────────────────────────────────────────────
// 12. BARRA DE CONTEXTO
// ─────────────────────────────────────────────────────────────────────────────

function updateContextBar() {
    const bar = document.getElementById('rm-context-bar');
    if (!bar) return;

    bar.innerHTML = '';

    // Trayectorias profesionalizantes
    const profLabels = { '207': 'Tray. Prof. 1', '208': 'Tray. Prof. 2' };
    for (const [slotPk, trackUmbrellaPk] of Object.entries(state.selections.prof_track)) {
        const label   = profLabels[slotPk];
        const hasSelection = trackUmbrellaPk !== null;
        const trackData    = hasSelection ? D.tracks[String(trackUmbrellaPk)] : null;
        const name         = trackData ? trackData.name : 'Sin seleccionar';
        const color        = hasSelection ? '#28a745' : '#3a3d4a';

        bar.appendChild(buildContextBadge(label, name, 'fa-road', color, () => {
            openProfTrackModal({ id: parseInt(slotPk), name: label }, 6, slotPk);
        }));
    }

    // Línea de énfasis
    const empSelection = state.selections.emphasis['211'];
    const empLinePk    = empSelection !== null ? D.emphasis_umbrella_to_line[String(empSelection)] : null;
    const empLineData  = empLinePk ? D.emphasis_lines[String(empLinePk)] : null;
    const empName      = empLineData ? empLineData.name : 'Sin seleccionar';
    const empColor     = empSelection !== null ? '#2ecc71' : '#3a3d4a';

    bar.appendChild(buildContextBadge('Línea de Énfasis', empName, 'fa-compass', empColor, () => {
        openEmphasisModal({ id: 211, name: 'Línea de Énfasis' }, 9);
    }));

    // NFI seleccionados
    const nfiLabels = { '23': 'NFI 3', '24': 'NFI 4', '25': 'NFI 5' };
    for (const [pk, selId] of Object.entries(state.selections.nfi)) {
        if (selId === null) continue;
        const c     = getCourse(selId);
        const name  = c ? c.name.substring(0, 28) : String(selId);
        const label = nfiLabels[pk] || 'NFI';
        const semNum = D.course_map[pk]?.semester_suggested || 2;

        bar.appendChild(buildContextBadge(label, name, 'fa-university', '#fd7e14', () => {
            openNFIElectivaModal({ id: parseInt(pk), name: label }, semNum, 'nfi');
        }));
    }

    // Electivas seleccionadas
    const electLabels = { '26': 'Elect. Mat. 1', '32': 'Elect. Mat. 2' };
    for (const [pk, selId] of Object.entries(state.selections.electiva)) {
        if (selId === null) continue;
        const c     = getCourse(selId);
        const name  = c ? c.name.substring(0, 28) : String(selId);
        const label = electLabels[pk] || 'Electiva';
        const semNum = D.course_map[pk]?.semester_suggested || 4;

        bar.appendChild(buildContextBadge(label, name, 'fa-calculator', '#4a90e2', () => {
            openNFIElectivaModal({ id: parseInt(pk), name: label }, semNum, 'electiva');
        }));
    }
}

function buildContextBadge(label, name, icon, color, onClick) {
    const badge = document.createElement('div');
    badge.className = 'rm-ctx-badge';
    badge.style.borderColor = color;
    badge.innerHTML = `
        <i class="fas ${icon} me-1" style="color:${color};font-size:0.75rem;"></i>
        <span class="rm-ctx-label">${label}:</span>
        <span class="rm-ctx-name">${name}</span>
        <i class="fas fa-pen rm-ctx-edit" style="color:${color};"></i>
    `;
    badge.addEventListener('click', onClick);
    return badge;
}

// ─────────────────────────────────────────────────────────────────────────────
// 13. BARRA DE SCROLL HORIZONTAL SUPERIOR Y BOTONES DE DESPLAZAMIENTO
// ─────────────────────────────────────────────────────────────────────────────

function initTopScrollbar() {
    if (document.querySelector('.roadmap-wrapper-outer')) return;

    const wrapper = document.querySelector('.roadmap-wrapper');
    if (!wrapper) return;

    const outer = document.createElement('div');
    outer.className = 'roadmap-wrapper-outer';
    wrapper.parentNode.insertBefore(outer, wrapper);
    outer.appendChild(wrapper);
}

function initScrollButtons() {
    if (document.querySelector('.rm-scroll-buttons')) return;
    
    const scrollEl = getScrollElement();
    if (!scrollEl) return;

    const container = document.createElement('div');
    container.className = 'rm-scroll-buttons';
    container.innerHTML = `
        <button class="rm-scroll-btn rm-scroll-btn-left" title="Desplazar izquierda">
            <i class="fas fa-chevron-left"></i>
        </button>
        <button class="rm-scroll-btn rm-scroll-btn-right" title="Desplazar derecha">
            <i class="fas fa-chevron-right"></i>
        </button>
    `;

    // Insertar después del outer (que contiene el wrapper)
    const outer = document.querySelector('.roadmap-wrapper-outer') ||
                  document.querySelector('.roadmap-wrapper');
    outer.after(container);

    const leftBtn  = container.querySelector('.rm-scroll-btn-left');
    const rightBtn = container.querySelector('.rm-scroll-btn-right');
    const STEP = 300;
    let interval = null;

    function doScroll(direction) {
        const el = getScrollElement();
        if (el) el.scrollLeft += direction * STEP;
    }

    function startScroll(direction) {
        doScroll(direction);
        interval = setInterval(() => doScroll(direction), 200);
    }

    function stopScroll() {
        clearInterval(interval);
        interval = null;
    }

    leftBtn.addEventListener('mousedown',  (e) => { e.preventDefault(); startScroll(-1); });
    rightBtn.addEventListener('mousedown', (e) => { e.preventDefault(); startScroll(1); });
    document.addEventListener('mouseup',   stopScroll);
    leftBtn.addEventListener('touchstart',  (e) => { startScroll(-1); e.preventDefault(); }, { passive: false });
    rightBtn.addEventListener('touchstart', (e) => { startScroll(1);  e.preventDefault(); }, { passive: false });
    document.addEventListener('touchend',   stopScroll);
}

// ─────────────────────────────────────────────────────────────────────────────
// 14. SCROLL AUTOMÁTICO AL ARRASTRAR CURSOS (DRAG & DROP)
// ─────────────────────────────────────────────────────────────────────────────

function initDragAutoScroll() {
    const ZONE    = 300;  
    const MAX_SPD = 50;   
    let scrollInterval = null;

    function stopAutoScroll() {
        if (scrollInterval) { clearInterval(scrollInterval); scrollInterval = null; }
    }

    function startAutoScroll(speed) {
        stopAutoScroll();
        scrollInterval = setInterval(() => {
            const el = getScrollElement();
            if (el) el.scrollLeft += speed;
        }, 16);
    }

    function handleMove(clientX) {
        const isDragging = !!document.querySelector('.course-card--chosen, .course-card--drag, .sortable-ghost');
        if (!isDragging) { stopAutoScroll(); return; }

        // Usar el ancho TOTAL de la ventana, no solo el contenedor
        const screenWidth = window.innerWidth;
        const distRight   = screenWidth - clientX;
        const distLeft    = clientX;

        if (distRight < ZONE) {
            startAutoScroll(Math.round(MAX_SPD * (1 - distRight / ZONE)));
        } else if (distLeft < ZONE) {
            startAutoScroll(-Math.round(MAX_SPD * (1 - distLeft / ZONE)));
        } else {
            stopAutoScroll();
        }
    }

    document.addEventListener('dragover',     (e) => handleMove(e.clientX));
    document.addEventListener('pointermove',  (e) => handleMove(e.clientX));
    document.addEventListener('touchmove',    (e) => {
        if (e.touches[0]) handleMove(e.touches[0].clientX);
    }, { passive: true });

    document.addEventListener('dragend',       stopAutoScroll);
    document.addEventListener('pointerup',     stopAutoScroll);
    document.addEventListener('pointercancel', stopAutoScroll);
    document.addEventListener('touchend',      stopAutoScroll);
}

// ─────────────────────────────────────────────────────────────────────────────
// 15. ONBOARDING / AYUDA INICIAL
// ─────────────────────────────────────────────────────────────────────────────

function initOnboarding() {
    const SEEN_KEY = 'careermap_onboarding_seen';

    function buildBanner() {
        const existing = document.getElementById('rm-onboarding-banner');
        if (existing) {
            existing.style.opacity = '0';
            existing.style.transition = 'opacity 0.3s';
            setTimeout(() => existing.remove(), 300);
            return null;
        }

        const banner = document.createElement('div');
        banner.id = 'rm-onboarding-banner';
        banner.className = 'rm-onboarding';
        banner.innerHTML = `
            <div class="rm-onboarding-icon">
                <i class="fas fa-circle-info"></i>
            </div>
            <div class="rm-onboarding-content">
                <div class="rm-onboarding-title">¿Cómo usar el roadmap?</div>
                <ul class="rm-onboarding-list">
                    <li><i class="fas fa-hand-pointer"></i> Haz click en cualquier curso para ver sus detalles</li>
                    <li><i class="fas fa-border-all"></i> Las tarjetas punteadas (<b style="color:#fff;">▾ ELEGIR</b>) requieren que elijas una opción</li>
                    <li><i class="fas fa-up-down-left-right"></i> Arrastra cualquier curso para cambiarlo de semestre</li>
                    <li><i class="fas fa-road"></i> Usa la barra superior para gestionar trayectorias y énfasis</li>
                    <li><i class="fas fa-triangle-exclamation" style="color:#f97316;"></i> Advertencias naranja/moradas indican prereqs o correqs pendientes</li>
                    <li><i class="fas fa-rotate-left" style="color:#ef4444;"></i> "Reiniciar" devuelve el roadmap a su estado original</li>
                </ul>
            </div>
            <button class="rm-onboarding-close" title="Cerrar ayuda">
                <i class="fas fa-xmark"></i>
            </button>
        `;

        banner.querySelector('.rm-onboarding-close').addEventListener('click', () => {
            banner.style.opacity = '0';
            banner.style.transition = 'opacity 0.3s';
            setTimeout(() => banner.remove(), 300);
            sessionStorage.setItem(SEEN_KEY, '1');
        });

        return banner;
    }

    // Conectar el botón de info que ya está en el DOM
    const infoBtn = document.getElementById('rm-info-btn');
    if (infoBtn) {
        infoBtn.addEventListener('click', () => {
            const existing = document.getElementById('rm-onboarding-banner');
            if (existing) {
                existing.style.opacity = '0';
                existing.style.transition = 'opacity 0.3s';
                setTimeout(() => existing.remove(), 300);
                return;
            }

            const banner = document.createElement('div');
            banner.id = 'rm-onboarding-banner';
            banner.className = 'rm-onboarding';
            banner.innerHTML = `
                <div class="rm-onboarding-icon">
                    <i class="fas fa-circle-info"></i>
                </div>
                <div class="rm-onboarding-content">
                    <div class="rm-onboarding-title">¿Cómo usar el roadmap?</div>
                    <ul class="rm-onboarding-list">
                        <li><i class="fas fa-hand-pointer"></i> Haz click en cualquier curso para ver sus detalles</li>
                        <li><i class="fas fa-border-all"></i> Las tarjetas punteadas (<b style="color:#fff;">▾ ELEGIR</b>) requieren que elijas una opción</li>
                        <li><i class="fas fa-up-down-left-right"></i> Arrastra cualquier curso para cambiarlo de semestre</li>
                        <li><i class="fas fa-road"></i> Usa la barra superior para gestionar trayectorias y énfasis</li>
                        <li><i class="fas fa-triangle-exclamation" style="color:#f97316;"></i> Advertencias naranja/moradas indican prereqs o correqs pendientes</li>
                        <li><i class="fas fa-rotate-left" style="color:#ef4444;"></i> "Reiniciar" devuelve el roadmap a su estado original</li>
                    </ul>
                </div>
                <button class="rm-onboarding-close" title="Cerrar ayuda">
                    <i class="fas fa-xmark"></i>
                </button>
            `;

            banner.querySelector('.rm-onboarding-close').addEventListener('click', () => {
                banner.style.opacity = '0';
                banner.style.transition = 'opacity 0.3s';
                setTimeout(() => banner.remove(), 300);
            });

            // Insertar justo antes del wrapper de contexto
            const ref = document.getElementById('rm-context-bar-wrapper');
            if (ref && ref.parentNode) {
                ref.parentNode.insertBefore(banner, ref);
                requestAnimationFrame(() => {
                    requestAnimationFrame(() => {
                        banner.style.opacity = '1';
                    });
                });
            }
        });
    }

    // Mostrar automáticamente solo si nunca se ha visto
    if (!sessionStorage.getItem(SEEN_KEY)) {
        const ctxWrapper = document.getElementById('rm-context-bar-wrapper');
        const banner = buildBanner();
        if (banner && ctxWrapper) {
            ctxWrapper.parentNode.insertBefore(banner, ctxWrapper);
            requestAnimationFrame(() => {
                requestAnimationFrame(() => {
                    banner.style.opacity = '1';
                });
            });
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// 16. INICIALIZACIÓN
// ─────────────────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', function() {
    // Paso 1: mover modales estáticos al body
    const staticModals = document.getElementById('rm-static-modals');
    if (staticModals) {
        staticModals.querySelectorAll('.modal').forEach(m => document.body.appendChild(m));
        staticModals.remove();
    }

    // Paso 2: crear modal de selección compartido
    createSelectionModalDOM();

    // Paso 3: crear wrapper de contexto
    const roadmapWrapper = document.querySelector('.roadmap-wrapper');
    if (roadmapWrapper && !document.getElementById('rm-context-bar-wrapper')) {
        const wrapper = document.createElement('div');
        wrapper.id = 'rm-context-bar-wrapper';
        wrapper.className = 'rm-context-bar-wrapper';
        wrapper.innerHTML = `
            <div id="rm-context-bar" class="rm-context-bar"></div>
            <div style="display:flex;align-items:center;gap:0.5rem;flex-shrink:0;">
                <button id="rm-info-btn" class="btn btn-sm rm-info-btn" title="Ver guía de uso">
                    <i class="fas fa-circle-info"></i>
                </button>
                <button id="rm-reset-btn" class="btn btn-outline-danger btn-sm rm-reset-btn">
                    <i class="fas fa-undo me-1"></i>Reiniciar
                </button>
            </div>
        `;
        roadmapWrapper.parentNode.insertBefore(wrapper, roadmapWrapper);
        document.getElementById('rm-reset-btn').addEventListener('click', () => {
            bootstrap.Modal.getOrCreateInstance(
                document.getElementById('rm-confirm-modal')
            ).show();
        });
    }

    // Paso 4: cargar estado y renderizar
    initFromServer().then(function(loadedFromServer) {
        if (!loadedFromServer) {
            const loadedFromSession = loadState();
            if (!loadedFromSession) {
                state = buildInitialState();
            }
        }
        rebuildAllSemesters();
        updateContextBar();
        validateAll();
        initTopScrollbar();
        initScrollButtons();
        initDragAutoScroll();
        initOnboarding();
    }).catch(function(e) {
        console.error('Error iniciando roadmap:', e);
        state = buildInitialState();
        rebuildAllSemesters();
        updateContextBar();
        validateAll();
        initTopScrollbar();
        initScrollButtons();
        initDragAutoScroll();
        initOnboarding();
    });
});