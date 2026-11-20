
from tutoria.encuesta import CAMPOS, PREGUNTAS


def test_trece_preguntas_y_campos():
    assert len(PREGUNTAS) == 13
    assert len(CAMPOS) == 7 + 12
