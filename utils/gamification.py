# utils/gamification.py
# Contém as definições de pontuação, limites e mapeamento de nomes elegantes.

# Pontuação por tipo de ação
PONTUACAO = {
    "checkin": 10,
    "checkout": 5,
    "missao": 20,
    "insta_engage": 2,
    "whatsapp": 1,
    "talk_team": 3,
}

# Limite diário por tipo de ação (None → ilimitado)
LIMITE_DIARIO = {
    "checkin": None,
    "checkout": None,
    "missao": 3,
    "insta_engage": 5,
    "whatsapp": 5,
    "talk_team": 5,
}

# Mapeamento de nomes brutos → nomes elegantes (usado na UI)
ACTION_LABELS = {
    "checkin":      "Check‑in",
    "checkout":     "Check‑out",
    "missao":       "Missão",
    "insta_engage":"Engajamento Instagram",
    "whatsapp":     "WhatsApp",
    "talk_team":    "Talk‑Team",
}
