# utils/gamification.py
# ==============================================================
# G A M I F I C A Ç Ã O   –   D I C I O N Á R I O   D E   P O N T O S
# ==============================================================

# -------------------  P O N T U A Ç Ã O  -----------------------
# Chave = código interno da ação (usado pelo wrapper)
# Valor = número de pontos a serem somados
PONTUACAO = {
    "checkin":      5,
    "checkout":     5,
    "missao":       8,
    "insta_engage": 4,
    "whatsapp":  10,
    "talk_team":    6,   # ← ponto para o supervisor que fala com a equipe
}

# -------------------  L I M I T E S   D I Á R I O S  -----------------------
# Chave = código interno da ação
# Valor = quantidade máxima de vezes que a ação pode gerar ponto **por dia**
# (None ou 0 → sem limite)
LIMITE_DIARIO = {
    "checkin":      1,
    "checkout":    1,
    "missao":       1,
    "insta_engage": 3,
    "colaborador":   1,
    "talk_team":    1,   # apenas 1 ponto por dia para o supervisor
}
