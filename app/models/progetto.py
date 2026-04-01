from app import db
from datetime import datetime

class ProgettoPSN(db.Model):
    __tablename__ = 'progetti_psn'
    
    id = db.Column(db.Integer, primary_key=True)
    anno_assegnazione = db.Column(db.Integer, nullable=False)
    anno_riferimento = db.Column(db.Integer, nullable=False)
    conti_aziendali = db.Column(db.String(255))  # Memorizzati come stringa separata da virgole o JSON
    azioni = db.Column(db.Text)
    referenti = db.Column(db.String(255))
    quota_assegnata = db.Column(db.Float, default=0.0)
    stato = db.Column(db.String(50), default='capienza') # capienza, superata, sterilizzato
    
    # Relazione con le assegnazioni degli impegni
    assegnazioni = db.relationship('AssegnazioneImpegno', backref='progetto', lazy='dynamic')

    @property
    def disponibilita_odierna(self):
        # Quota - Impegni con determina (effettivi)
        impegni_deliberati = sum(a.costo_assegnato for a in self.assegnazioni 
                                 if a.impegno.stato_logico == 'assegnato' and a.impegno.num_determina)
        return self.quota_assegnata - impegni_deliberati

    @property
    def disponibilita_con_impegni(self):
        # Quota - Tutti gli impegni attivi (programmati + deliberati)
        impegni_totali = sum(a.costo_assegnato for a in self.assegnazioni 
                             if a.impegno.stato_logico == 'assegnato')
        return self.quota_assegnata - impegni_totali
    
    @property
    def calcola_stato(self):
        disp = self.disponibilita_con_impegni
        if self.stato == 'sterilizzato':
            return 'sterilizzato'
        if disp < 0:
            return 'capienza superata'
        return 'capienza'

    @property
    def badge_colore(self):
        stato = self.calcola_stato
        if stato == 'capienza superata': return 'bg-danger'
        if stato == 'sterilizzato': return 'bg-secondary'
        return 'bg-success'