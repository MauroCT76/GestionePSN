from flask import Blueprint, render_template, request, jsonify, redirect, url_for, send_file
from app import db
from app.models.progetto import ProgettoPSN
from app.models.impegno import Impegno, AssegnazioneImpegno
from app.utils.excel_handler import import_psn_from_excel, export_to_original_format
import io
import pandas as pd
from datetime import datetime

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    progetti = ProgettoPSN.query.all()
    impegni_liberi = Impegno.query.filter_by(stato_logico='da_assegnare').all()
    return render_template('dashboard.html', progetti=progetti, impegni_liberi=impegni_liberi)

@main_bp.route('/import/excel', methods=['POST'])
def import_excel():
    if 'file' not in request.files:
        return redirect(url_for('main.index'))
    file = request.files['file']
    if file.filename == '':
        return redirect(url_for('main.index'))
    import_psn_from_excel(file)
    return redirect(url_for('main.index'))

@main_bp.route('/export/excel')
def export_excel():
    df = export_to_original_format()
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Rendicontazione')
    output.seek(0)
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='Rendicontazione_PSN.xlsx'
    )

@main_bp.route('/api/impegno/nuovo', methods=['POST'])
def nuovo_impegno():
    data = request.form
    titolo = data.get('titolo')
    costo = data.get('costo_previsto', 0)
    tipo = data.get('tipo')
    
    nuovo = Impegno(
        tipo=tipo,
        titolo=titolo,
        costo_previsto=float(costo) if costo else 0.0,
        note=data.get('note'),
        numero_nota=data.get('numero_nota'),
        stato_logico='da_assegnare'
    )
    
    data_n = data.get('data_nota')
    nuovo.data_nota = datetime.strptime(data_n, '%Y-%m-%d').date() if data_n else None
    
    nuovo.num_determina = data.get('num_determina')
    data_d = data.get('data_determina')
    nuovo.data_determina = datetime.strptime(data_d, '%Y-%m-%d').date() if data_d else None
    
    c_det = data.get('costo_determina')
    nuovo.costo_determina = float(c_det) if c_det else None

    db.session.add(nuovo)
    db.session.commit()
    return redirect(url_for('main.index'))

@main_bp.route('/api/progetto/nuovo', methods=['POST'])
def nuovo_progetto():
    data = request.form
    nuovo_psn = ProgettoPSN(
        anno_assegnazione=int(data.get('anno_assegnazione', 2024)),
        anno_riferimento=int(data.get('anno_riferimento', 2024)),
        conti_aziendali=data.get('conti_aziendali', ''),
        azioni=data.get('azioni', ''),
        referenti=data.get('referenti', ''),
        quota_assegnata=float(data.get('quota_assegnata', 0.0)),
        stato='capienza'
    )
    db.session.add(nuovo_psn)
    db.session.commit()
    return redirect(url_for('main.index'))

@main_bp.route('/api/assegna_impegno', methods=['POST'])
def assegna_impegno():
    data = request.get_json()
    impegno_id = data.get('impegno_id')
    progetto_id = data.get('progetto_id')  
    vecchio_progetto_id = data.get('vecchio_progetto_id')
    
    impegno = Impegno.query.get_or_404(impegno_id)
    
    if vecchio_progetto_id and vecchio_progetto_id != 'null':
        assegnazione_attiva = AssegnazioneImpegno.query.filter_by(
            impegno_id=impegno_id, 
            progetto_id=vecchio_progetto_id, 
            storico=False
        ).first()
    else:
        assegnazione_attiva = None

    if not progetto_id or progetto_id == 'null':
        if assegnazione_attiva:
            assegnazione_attiva.storico = True
        se_ancora_attivo = AssegnazioneImpegno.query.filter_by(impegno_id=impegno_id, storico=False).first()
        if not se_ancora_attivo:
            impegno.stato_logico = 'da_assegnare'
    else:
        if assegnazione_attiva:
            if str(assegnazione_attiva.progetto_id) == str(progetto_id):
                return jsonify({"status": "success"})
            else:
                assegnazione_attiva.storico = True
                quota_spostata = assegnazione_attiva.costo_assegnato
        else:
            quota_spostata = impegno.costo_previsto
        
        assegnazione_target = AssegnazioneImpegno.query.filter_by(
            impegno_id=impegno_id, 
            progetto_id=progetto_id
        ).first()

        if assegnazione_target:
            assegnazione_target.storico = False
            assegnazione_target.costo_assegnato = quota_spostata
        else:
            nuova_ass = AssegnazioneImpegno(
                impegno_id=impegno_id,
                progetto_id=progetto_id,
                costo_assegnato=quota_spostata,
                storico=False
            )
            db.session.add(nuova_ass)
            
        impegno.stato_logico = 'assegnato'
        
    db.session.commit()
    return jsonify({"status": "success"})

@main_bp.route('/api/impegno/<int:id>', methods=['GET'])
def get_impegno(id):
    imp = Impegno.query.get_or_404(id)
    
    allocazioni = []
    for ass in imp.assegnazioni:
        if not ass.storico:
            allocazioni.append({
                'progetto_id': ass.progetto_id,
                'costo': ass.costo_assegnato
            })

    return jsonify({
        'id': imp.id,
        'titolo': imp.titolo,
        'tipo': imp.tipo,
        'costo_previsto': imp.costo_previsto,
        'note': imp.note or '',
        'numero_nota': imp.numero_nota or '',
        'data_nota': imp.data_nota.strftime('%Y-%m-%d') if imp.data_nota else '',
        'num_determina': imp.num_determina or '',
        'data_determina': imp.data_determina.strftime('%Y-%m-%d') if imp.data_determina else '',
        'costo_determina': imp.costo_determina or '',
        'allocazioni': allocazioni
    })

@main_bp.route('/api/impegno/<int:id>/edit', methods=['POST'])
def edit_impegno(id):
    imp = Impegno.query.get_or_404(id)
    data = request.form
    
    imp.titolo = data.get('titolo')
    imp.tipo = data.get('tipo')
    imp.costo_previsto = float(data.get('costo_previsto') or 0.0)
    imp.note = data.get('note')
    imp.numero_nota = data.get('numero_nota')
    
    data_n = data.get('data_nota')
    imp.data_nota = datetime.strptime(data_n, '%Y-%m-%d').date() if data_n else None
    
    imp.num_determina = data.get('num_determina')
    data_d = data.get('data_determina')
    imp.data_determina = datetime.strptime(data_d, '%Y-%m-%d').date() if data_d else None
    
    c_det = data.get('costo_determina')
    imp.costo_determina = float(c_det) if c_det else None

    psn_ids = request.form.getlist('progetto_id[]')
    costi = request.form.getlist('costo_ripartito[]')
    
    if psn_ids and costi:
        nuove_quote = {int(p): float(c) for p, c in zip(psn_ids, costi) if p}
        assegnazioni_attive = AssegnazioneImpegno.query.filter_by(impegno_id=id, storico=False).all()
        
        for ass in assegnazioni_attive:
            if ass.progetto_id not in nuove_quote:
                ass.storico = True
            else:
                ass.costo_assegnato = nuove_quote[ass.progetto_id]
                del nuove_quote[ass.progetto_id] 
                
        for p_id, c in nuove_quote.items():
            ass_storica = AssegnazioneImpegno.query.filter_by(impegno_id=id, progetto_id=p_id, storico=True).first()
            if ass_storica:
                ass_storica.storico = False
                ass_storica.costo_assegnato = c
            else:
                nuova_ass = AssegnazioneImpegno(impegno_id=id, progetto_id=p_id, costo_assegnato=c, storico=False)
                db.session.add(nuova_ass)
                
    else:
        ass_attive = AssegnazioneImpegno.query.filter_by(impegno_id=id, storico=False).all()
        if len(ass_attive) == 1:
            ass_attive[0].costo_assegnato = imp.costo_previsto

    db.session.commit()
    return redirect(url_for('main.index'))

@main_bp.route('/api/impegno/<int:id>/delete', methods=['POST'])
def delete_impegno(id):
    imp = Impegno.query.get_or_404(id)
    db.session.delete(imp)
    db.session.commit()
    return redirect(url_for('main.index'))