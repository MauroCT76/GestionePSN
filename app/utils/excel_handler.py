import pandas as pd
from app.models.progetto import ProgettoPSN
from app import db

def import_psn_from_excel(file):
    try:
        df = pd.read_excel(file)
    except:
        file.seek(0)
        df = pd.read_csv(file, sep=None, engine='python')

    # Normalizziamo le colonne in minuscolo
    df.columns = [str(c).strip().lower() for c in df.columns]
    
    print("--- INIZIO IMPORTAZIONE ---")
    print("Colonne rilevate nel file:", df.columns.tolist())

    for index, row in df.iterrows():
        anno_ass = row.get('anno di assegnazione')
        
        # Se la riga è vuota la saltiamo
        if pd.isna(anno_ass) or str(anno_ass).strip() == '':
            continue
            
        # Tentiamo di convertire in numero. Se fallisce (es. c'è del testo), saltiamo la riga
        try:
            # Passiamo prima per float() per gestire casi come "2024.0" tipici di Excel
            anno_ass_int = int(float(anno_ass))
        except ValueError:
            print(f"Riga {index + 2} saltata: '{anno_ass}' non è un anno valido.")
            continue

        anno_rif = row.get('anno di riferimento')
        try:
            anno_rif_int = int(float(anno_rif)) if pd.notna(anno_rif) and str(anno_rif).strip() != '' else anno_ass_int
        except ValueError:
            anno_rif_int = anno_ass_int

        referente = str(row.get('referenti') or 'N/D')
        
        # Gestione quote
        quota_str = row.get("quota assegnata nell'anno") or 0
        try:
            quota = float(str(quota_str).replace(',', '.')) if pd.notna(quota_str) else 0.0
        except ValueError:
            quota = 0.0

        conti = str(row.get('conti aziendali') or '')
        azioni = str(row.get('azioni') or '')

        # Pulizia dei 'nan' di pandas
        if referente.lower() == 'nan': referente = ''
        if conti.lower() == 'nan': conti = ''
        if azioni.lower() == 'nan': azioni = ''

        esistente = ProgettoPSN.query.filter_by(
            anno_riferimento=anno_rif_int,
            referenti=referente
        ).first()

        if esistente:
            esistente.quota_assegnata = quota
            esistente.conti_aziendali = conti
            esistente.azioni = azioni
        else:
            nuovo_psn = ProgettoPSN(
                anno_assegnazione=anno_ass_int,
                anno_riferimento=anno_rif_int,
                conti_aziendali=conti,
                azioni=azioni,
                referenti=referente,
                quota_assegnata=quota,
                stato='capienza'
            )
            db.session.add(nuovo_psn)
    
    db.session.commit()
    print("--- IMPORTAZIONE COMPLETATA ---")

def export_to_original_format():
    progetti = ProgettoPSN.query.all()
    data = []
    
    for p in progetti:
        data.append({
            'Anno di assegnazione': p.anno_assegnazione,
            'Anno di riferimento': p.anno_riferimento,
            'Conti aziendali': p.conti_aziendali,
            'Azioni': p.azioni,
            'Referenti': p.referenti,
            'Quota assegnata nell\'anno': p.quota_assegnata,
            'Disponibilità odierna': p.disponibilita_odierna,
            'Disponibilita\' con impegni': p.disponibilita_con_impegni,
            'Stato': p.calcola_stato
        })
    
    return pd.DataFrame(data)