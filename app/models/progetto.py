from app import db
from datetime import datetime
import re

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
    
    # NUOVI CAMPI: Disponibilità comunicata dall'azienda
    disp_comunicata = db.Column(db.Float, nullable=True)
    data_disp_comunicata = db.Column(db.Date, nullable=True)
    
    assegnazioni = db.relationship('AssegnazioneImpegno', backref='progetto', lazy='dynamic')
    note_testuali = db.relationship('NotaPSN', backref='progetto', cascade="all, delete-orphan")

    @property
    def disponibilita_comunicata_effettiva(self):
        """Se l'azienda non ha ancora comunicato nulla, assumiamo che sia pari alla quota iniziale."""
        return self.disp_comunicata if self.disp_comunicata is not None else self.quota_assegnata

    @property
    def disponibilita_odierna(self):
        impegni_deliberati = sum(a.costo_assegnato for a in self.assegnazioni 
                                 if not a.storico and a.impegno.num_determina)
        return self.quota_assegnata - impegni_deliberati

    @property
    def disponibilita_con_impegni(self):
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

    @property
    def conto_principale(self):
        if not self.conti_aziendali:
            return "N/D"
        match = re.search(r'\b\d{8}\b', self.conti_aziendali)
        if match:
            return match.group(0)
        testo = str(self.conti_aziendali).strip()
        return (testo[:15] + '...') if len(testo) > 15 else testo


class NotaPSN(db.Model):
    __tablename__ = 'note_psn'
    
    id = db.Column(db.Integer, primary_key=True)
    progetto_id = db.Column(db.Integer, db.ForeignKey('progetti_psn.id'), nullable=False)
    testo = db.Column(db.Text, nullable=False)
    importante = db.Column(db.Boolean, default=False)
    data_creazione = db.Column(db.DateTime, default=datetime.utcnow)