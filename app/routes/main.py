from flask import Blueprint, render_template, request, jsonify, redirect, url_for, send_file
from app import db
from app.models.progetto import ProgettoPSN
from app.models.impegno import Impegno, AssegnazioneImpegno
from app.utils.excel_handler import import_psn_from_excel, export_to_original_format
import io
import pandas as pd

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
    titolo = request.form.get('titolo')
    costo = request.form.get('costo_previsto', 0)
    tipo = request.form.get('tipo')
    
    nuovo = Impegno(
        tipo=tipo,
        titolo=titolo,
        costo_previsto=float(costo) if costo else 0.0,
        stato_logico='da_assegnare'
    )
    db.session.add(nuovo)
    db.session.commit()
    return redirect(url_for('main.index'))

# --- NUOVA ROTTA PER CREAZIONE MANUALE PSN ---
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
    
    impegno = Impegno.query.get_or_404(impegno_id)
    assegnazione = AssegnazioneImpegno.query.filter_by(impegno_id=impegno_id).first()
    
    if assegnazione:
        assegnazione.progetto_id = progetto_id
    else:
        assegnazione = AssegnazioneImpegno(
            impegno_id=impegno_id,
            progetto_id=progetto_id,
            costo_assegnato=impegno.costo_previsto
        )
        db.session.add(assegnazione)
    
    impegno.stato_logico = 'assegnato'
    db.session.commit()
    
    return jsonify({"status": "success"})