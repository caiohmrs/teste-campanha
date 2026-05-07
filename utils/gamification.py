# utils/gamification.py
# Contém as definições de pontuação, limites e mapeamento de nomes elegantes.

# Pontuação por tipo de ação
PONTUACAO = {
    "checkin": 5,
    "checkout": 5,
    "missao": 10,
    "insta_engage": 2,
    "whatsapp": 10,

}

# Limite diário por tipo de ação (None → ilimitado)
LIMITE_DIARIO = {
    "checkin": 1,
    "checkout": 1,
    "missao": 1,
    "insta_engage": 3,
    "whatsapp": 1,

}

# Mapeamento de nomes brutos → nomes elegantes (usado na UI)
ACTION_LABELS = {
    "checkin":      "Realizar Check‑in Diário",
    "checkout":     "Realizar Check‑out Diário",
    "missao":       "Concluir a Missão do Dia",
    "insta_engage":"Curtir, Comentar e Compartilhar no Instagram",
    "whatsapp":     "Chamar um novo amigo para a campanha pelo WhatsApp",

}
