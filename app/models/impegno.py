from app import db
from datetime import datetime

class Impegno(db.Model):
    __tablename__ = 'impegni'
    
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(50))  # 'Personale', 'Materiale'
    titolo = db.Column(db.String(255), nullable=False)
    costo_previsto = db.Column(db.Float, default=0.0)
    
    # Dati determina (se presenti)
    data_determina = db.Column(db.Date, nullable=True)
    num_determina = db.Column(db.String(50), nullable=True)
    costo_determina = db.Column(db.Float, nullable=True)
    pagamenti_effettuati = db.Column(db.Float, default=0.0)
    
    # Stato logico: 'da_assegnare', 'assegnato', 'storico'
    stato_logico = db.Column(db.String(50), default='da_assegnare')
    
    assegnazioni = db.relationship('AssegnazioneImpegno', backref='impegno', cascade="all, delete-orphan")

class AssegnazioneImpegno(db.Model):
    """Tabella pivot per gestire la divisione di un impegno su più PSN e lo storico"""
    __tablename__ = 'assegnazioni_impegni'
    
    id = db.Column(db.Integer, primary_key=True)
    impegno_id = db.Column(db.Integer, db.ForeignKey('impegni.id'), nullable=False)
    progetto_id = db.Column(db.Integer, db.ForeignKey('progetti_psn.id'), nullable=False)
    costo_assegnato = db.Column(db.Float, nullable=False) # Quota parte dell'impegno su questo PSN
    data_creazione = db.Column(db.DateTime, default=datetime.utcnow)