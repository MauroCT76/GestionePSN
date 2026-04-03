const listaPSN = window.APP_DATA.listaPSN;

// --- GESTIONE NOTE PSN ---
let currentNotePsnId = null;
let modalNotePSN = null;

document.addEventListener('DOMContentLoaded', () => {
    modalNotePSN = new bootstrap.Modal(document.getElementById('modalNotePSN'));
});

function apriNotePSN(id) {
    currentNotePsnId = id;
    document.getElementById('nuovaNotaTesto').value = '';
    document.getElementById('nuovaNotaImportante').checked = false;
    caricaNotePSN();
    modalNotePSN.show();
}

function caricaNotePSN() {
    fetch(`/api/progetto/${currentNotePsnId}/note`)
        .then(res => res.json())
        .then(note => {
            const container = document.getElementById('listaNotePSN');
            container.innerHTML = '';
            if (note.length === 0) {
                container.innerHTML = '<div class="text-center text-muted small py-3">Nessuna nota presente.</div>';
                return;
            }
            note.forEach(n => {
                const starClass = n.importante ? 'fas text-warning' : 'far text-secondary';
                const bgClass = n.importante ? 'bg-white border border-warning' : 'bg-white border-0';
                container.innerHTML += `
                    <div class="card mb-2 ${bgClass} shadow-sm">
                        <div class="card-body p-2 d-flex justify-content-between align-items-start">
                            <div style="flex-grow: 1; font-size: 0.9rem;" class="me-2">
                                ${n.testo.replace(/\n/g, '<br>')}
                                <div class="text-muted" style="font-size: 0.65rem; margin-top: 5px;">${n.data_creazione}</div>
                            </div>
                            <div class="d-flex flex-column gap-2 text-end">
                                <i class="${starClass} fa-star" style="cursor:pointer;" onclick="toggleStellaNota(${n.id})" title="Segna/Rimuovi Importante"></i>
                                <i class="fas fa-trash text-danger" style="cursor:pointer;" onclick="eliminaNota(${n.id})" title="Elimina"></i>
                            </div>
                        </div>
                    </div>
                `;
            });
        });
}

function salvaNotaPSN() {
    const testo = document.getElementById('nuovaNotaTesto').value.trim();
    const importante = document.getElementById('nuovaNotaImportante').checked;
    if(!testo) return;

    fetch(`/api/progetto/${currentNotePsnId}/note`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ testo: testo, importante: importante })
    }).then(res => res.json()).then(data => {
        if(data.status === 'success') {
            document.getElementById('nuovaNotaTesto').value = '';
            document.getElementById('nuovaNotaImportante').checked = false;
            caricaNotePSN();
        }
    });
}

function toggleStellaNota(id) {
    fetch(`/api/nota/${id}/toggle`, { method: 'POST' })
        .then(res => res.json())
        .then(() => caricaNotePSN());
}

function eliminaNota(id) {
    if(confirm('Eliminare definitivamente questa nota?')) {
        fetch(`/api/nota/${id}/delete`, { method: 'POST' })
            .then(res => res.json())
            .then(() => caricaNotePSN());
    }
}

// --- FILTRI DASHBOARD ---
const filterText = document.getElementById('filterText');
const filterAnno = document.getElementById('filterAnno');
const psnCards = document.querySelectorAll('.psn-card');

function applicaFiltri() {
    const textVal = filterText.value.toLowerCase();
    const annoVal = filterAnno.value;
    psnCards.forEach(card => {
        const cardAnno = card.getAttribute('data-anno');
        const cardTesto = card.getAttribute('data-testo');
        const matchText = cardTesto.includes(textVal);
        const matchAnno = (annoVal === "" || cardAnno === annoVal);
        if (matchText && matchAnno) { card.style.display = 'flex'; } 
        else { card.style.display = 'none'; }
    });
}

function resetFiltri() {
    filterText.value = "";
    filterAnno.value = "";
    applicaFiltri();
}

if(filterText) filterText.addEventListener('input', applicaFiltri);
if(filterAnno) filterAnno.addEventListener('change', applicaFiltri);

// --- DRAG & DROP (SORTABLE.JS) ---
document.addEventListener('DOMContentLoaded', () => {
    const containers = document.querySelectorAll('.pila-impegni');
    containers.forEach(container => {
        new Sortable(container, {
            group: 'psn-group',
            animation: 150,
            fallbackOnBody: true,
            swapThreshold: 0.65,
            filter: '.storico, .locked',
            onAdd: function (evt) {
                const impegnoId = evt.item.getAttribute('data-id');
                const nuovoPsnId = evt.to.getAttribute('data-psn-id');
                const vecchioPsnId = evt.from.getAttribute('data-psn-id');
                fetch('/api/assegna_impegno', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ impegno_id: impegnoId, progetto_id: nuovoPsnId, vecchio_progetto_id: vecchioPsnId })
                }).then(res => res.json()).then(data => { window.location.reload(); });
            }
        });
    });
});

// --- FUNZIONI MODALI PRINCIPALI ---
let modalDettaglioImpegno = null;
let modalDettaglioPSN = null;
let modalDisp = null;

document.addEventListener('DOMContentLoaded', () => {
    modalDettaglioImpegno = new bootstrap.Modal(document.getElementById('modalDettaglioImpegno'));
    modalDettaglioPSN = new bootstrap.Modal(document.getElementById('modalDettaglioPSN'));
    modalDisp = new bootstrap.Modal(document.getElementById('modalDispComunicata'));
});

// --- NUOVO: MODIFICA RAPIDA DISPONIBILITA' ---
function apriModificaDisp(id, currentVal, currentDate) {
    document.getElementById('formEditDisp').action = `/api/progetto/${id}/disp`;
    document.getElementById('edit_disp_comunicata').value = currentVal;
    
    if(currentDate) {
        document.getElementById('edit_data_disp').value = currentDate;
    } else {
        document.getElementById('edit_data_disp').value = new Date().toISOString().split('T')[0];
    }
    
    modalDisp.show();
}

// --- Progetti PSN ---
function apriNuovoProgetto() {
    document.getElementById('formEditPSN').reset();
    document.getElementById('formEditPSN').action = '/api/progetto/nuovo';
    document.getElementById('psn_anno_assegnazione').value = new Date().getFullYear();
    document.getElementById('psn_anno_riferimento').value = new Date().getFullYear();
    document.getElementById('modalPSNTitle').innerHTML = '<i class="fas fa-folder-plus me-2"></i>Nuovo Progetto PSN';
    document.getElementById('btnEliminaPSN').style.display = 'none';
    modalDettaglioPSN.show();
}

function apriDettaglioProgetto(id) {
    document.getElementById('formEditPSN').reset();
    document.getElementById('formEditPSN').action = `/api/progetto/${id}/edit`;
    document.getElementById('formDeletePSN').action = `/api/progetto/${id}/delete`;
    document.getElementById('modalPSNTitle').innerHTML = '<i class="fas fa-edit me-2"></i>Modifica Progetto PSN';
    document.getElementById('btnEliminaPSN').style.display = 'block';

    fetch(`/api/progetto/${id}`)
        .then(res => res.json())
        .then(data => {
            document.getElementById('psn_anno_assegnazione').value = data.anno_assegnazione;
            document.getElementById('psn_anno_riferimento').value = data.anno_riferimento;
            document.getElementById('psn_referenti').value = data.referenti;
            document.getElementById('psn_quota_assegnata').value = data.quota_assegnata;
            document.getElementById('psn_conti_aziendali').value = data.conti_aziendali;
            document.getElementById('psn_azioni').value = data.azioni;
            document.getElementById('psn_disp_comunicata').value = data.disp_comunicata;
            document.getElementById('psn_data_disp_comunicata').value = data.data_disp_comunicata;
            modalDettaglioPSN.show();
        });
}

function eliminaProgetto() {
    if(confirm("Sei sicuro di voler eliminare questo Progetto PSN? Tutte le spese in esso contenute verranno rimesse in 'Da Assegnare'.")) {
        document.getElementById('formDeletePSN').submit();
    }
}

// --- Impegni ---
function toggleCustomTipo(val) {
    const customInput = document.getElementById('edit_tipo_custom');
    if(val === 'custom') {
        customInput.style.display = 'block'; customInput.required = true;
    } else {
        customInput.style.display = 'none'; customInput.required = false; customInput.value = '';
    }
}

function cambiaTipoUfficializzazione(tipo) {
    document.getElementById('lbl_num_ufficializzazione').innerText = "Numero " + tipo;
    document.getElementById('lbl_data_ufficializzazione').innerText = "Data " + tipo;
}

function impostaStatoCampi(isDefinitivo) {
    const campiDaBloccare = [
        'edit_titolo', 'edit_costo_previsto', 'edit_numero_nota', 'edit_data_nota',
        'edit_num_determina', 'edit_data_determina', 'edit_costo_determina'
    ];
    campiDaBloccare.forEach(id => {
        const el = document.getElementById(id);
        if(el) el.readOnly = isDefinitivo;
    });

    document.getElementById('edit_tipo_select').disabled = isDefinitivo;
    document.getElementById('edit_tipo_custom').readOnly = isDefinitivo;
    document.getElementById('radioDetermina').disabled = isDefinitivo;
    document.getElementById('radioDelibera').disabled = isDefinitivo;

    if(isDefinitivo) {
        document.getElementById('btnAggiungiRipartizione').style.display = 'none';
        document.getElementById('alertDefinitivo').style.display = 'block';
        document.getElementById('btnEliminaImpegno').style.display = 'none';
        document.getElementById('testo-ripartizione').innerText = 'Quote attuali (Sola lettura):';
    } else {
        document.getElementById('btnAggiungiRipartizione').style.display = 'inline-block';
        document.getElementById('alertDefinitivo').style.display = 'none';
        document.getElementById('btnEliminaImpegno').style.display = 'block';
        document.getElementById('testo-ripartizione').innerText = "Da qui puoi spezzare l'impegno assegnando quote diverse a conti diversi.";
    }
}

function apriNuovoImpegno() {
    document.getElementById('formEditImpegno').reset();
    document.getElementById('formEditImpegno').action = '/api/impegno/nuovo';
    document.getElementById('modalImpegnoTitle').innerHTML = '<i class="fas fa-plus-circle me-2"></i>Nuova Tessera Impegno';
    document.getElementById('sezione-ripartizione').style.display = 'none'; 
    document.getElementById('edit_tipo_select').value = 'Personale';
    toggleCustomTipo('Personale');
    
    document.getElementById('radioDetermina').checked = true;
    cambiaTipoUfficializzazione('Determina');
    
    impostaStatoCampi(false);
    document.getElementById('btnEliminaImpegno').style.display = 'none'; 
    modalDettaglioImpegno.show();
}

function creaRigaRipartizione(psnIdSelezionato, costo, isDefinitivo) {
    let options = '<option value="">Seleziona un Progetto PSN...</option>';
    listaPSN.forEach(p => {
        options += `<option value="${p.id}" ${p.id == psnIdSelezionato ? 'selected' : ''}>${p.titolo}</option>`;
    });

    return `
        <div class="row ripartizione-riga mb-2 align-items-center">
            <div class="col-8">
                <select name="progetto_id[]" class="form-select form-select-sm" required ${isDefinitivo ? 'disabled' : ''}>
                    ${options}
                </select>
            </div>
            <div class="col-3">
                <input type="number" name="costo_ripartito[]" class="form-control form-control-sm" value="${costo}" step="0.01" placeholder="Quota €" required ${isDefinitivo ? 'readonly' : ''}>
            </div>
            <div class="col-1 text-end">
                <button type="button" class="btn btn-sm btn-outline-danger border-0" onclick="this.closest('.ripartizione-riga').remove()" style="display: ${isDefinitivo ? 'none' : 'inline-block'};">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        </div>
    `;
}

function aggiungiRigaRipartizione() {
    document.getElementById('ripartizione-rows').insertAdjacentHTML('beforeend', creaRigaRipartizione('', '', false));
}

function apriDettaglioImpegno(id) {
    document.getElementById('formEditImpegno').reset();
    document.getElementById('formEditImpegno').action = `/api/impegno/${id}/edit`;
    document.getElementById('formDeleteImpegno').action = `/api/impegno/${id}/delete`;
    document.getElementById('modalImpegnoTitle').innerHTML = '<i class="fas fa-edit me-2"></i>Pannello Impegno';
    
    fetch(`/api/impegno/${id}`)
        .then(res => res.json())
        .then(data => {
            const isDefinitivo = (data.num_determina && data.num_determina.trim() !== '');
            impostaStatoCampi(isDefinitivo);

            document.getElementById('edit_titolo').value = data.titolo;
            const tipiStandard = ['Personale', 'Materiale', 'Altro'];
            if (tipiStandard.includes(data.tipo)) {
                document.getElementById('edit_tipo_select').value = data.tipo;
                toggleCustomTipo(data.tipo);
            } else {
                document.getElementById('edit_tipo_select').value = 'custom';
                toggleCustomTipo('custom');
                document.getElementById('edit_tipo_custom').value = data.tipo;
            }
            
            const tipoUff = data.tipo_ufficializzazione || 'Determina';
            if (tipoUff === 'Delibera') {
                document.getElementById('radioDelibera').checked = true;
            } else {
                document.getElementById('radioDetermina').checked = true;
            }
            cambiaTipoUfficializzazione(tipoUff);
            
            document.getElementById('edit_costo_previsto').value = data.costo_previsto;
            document.getElementById('edit_note').value = data.note;
            document.getElementById('edit_numero_nota').value = data.numero_nota;
            document.getElementById('edit_data_nota').value = data.data_nota;
            document.getElementById('edit_num_determina').value = data.num_determina;
            document.getElementById('edit_data_determina').value = data.data_determina;
            document.getElementById('edit_costo_determina').value = data.costo_determina;
            
            const divRipartizione = document.getElementById('sezione-ripartizione');
            const containerRows = document.getElementById('ripartizione-rows');
            containerRows.innerHTML = ''; 

            if (data.allocazioni && data.allocazioni.length > 0) {
                divRipartizione.style.display = 'block';
                data.allocazioni.forEach(all => {
                    containerRows.insertAdjacentHTML('beforeend', creaRigaRipartizione(all.progetto_id, all.costo, isDefinitivo));
                });
            } else {
                divRipartizione.style.display = 'none'; 
            }

            modalDettaglioImpegno.show();
        });
}

function eliminaImpegno() {
    if(confirm("Sei sicuro di voler eliminare definitivamente questo impegno e tutte le sue assegnazioni?")) {
        document.getElementById('formDeleteImpegno').submit();
    }
}