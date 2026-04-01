from app import create_app, db
from app.models.progetto import ProgettoPSN
from app.models.impegno import Impegno, AssegnazioneImpegno

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'ProgettoPSN': ProgettoPSN, 'Impegno': Impegno, 'AssegnazioneImpegno': AssegnazioneImpegno}

if __name__ == '__main__':
    app.run(debug=True)