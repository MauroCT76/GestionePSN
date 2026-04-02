# FILE: app/models/progetto.py
from app import db

class ProgettoPSN(db.Model):
    __tablename__ = 'progetti_psn'
    
    id = db.Column(db.Integer, primary_key=True)
    anno_assegnazione = db.Column(db.Integer, nullable=False)
    anno_riferimento = db.Column(db.Integer, nullable=False)
    conti_aziendali = db.Column(db.String(255))
    azioni = db.Column(db.Text)
    referenti = db.Column(db.String(255))
    quota_assegnata = db.Column(db.Float, default=0.0)
    stato = db.Column(db.String(50), default='capienza')
    
    assegnazioni = db.relationship('AssegnazioneImpegno', backref='progetto', lazy='dynamic')

    @property
    def disponibilita_odierna(self):
        # Escludiamo lo storico dal calcolo
        impegni_deliberati = sum(a.costo_assegnato for a in self.assegnazioni 
                                 if not a.storico and a.impegno.num_determina)
        return self.quota_assegnata - impegni_deliberati

    @property
    def disponibilita_con_impegni(self):
        # Escludiamo lo storico dal calcolo
        impegni_totali = sum(a.costo_assegnato for a in self.assegnazioni 
                             if not a.storico)
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