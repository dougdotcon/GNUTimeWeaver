# Prompt de Ideacao v2 (Reutilizavel)

Use este prompt para gerar novas ideias com qualidade consistente e formato pronto para execucao.

## Prompt base

"""
Atue como arquiteto de sistemas e pesquisador aplicado em 2026.

Objetivo:
Gerar [N] ideias originais e plausiveis para [SETOR/PROBLEMA], cada uma combinando exatamente 3 conceitos de dominios diferentes.

Regras obrigatorias:
1) Nao repetir ideias comuns de mercado nem recombinacoes triviais.
2) Priorizar propostas pouco exploradas, com potencial de validacao em 30-90 dias.
3) Nao depender de tecnologia inexistente; pode usar fronteira cientifica, mas com caminho de prototipo claro.
4) Em cada ideia, incluir risco tecnico, risco regulatorio e estrategia de mitigacao.
5) Sempre separar o que e sinal observavel, o que e inferencia e o que e decisao automatizada.

Formato de resposta (obrigatorio para cada ideia):
- Nome da ideia
- Tese em 1 frase
- Dor economica/operacional atacada
- Conceito 1 (origem disciplinar)
- Conceito 2 (origem disciplinar)
- Conceito 3 (origem disciplinar)
- Mecanismo de instrumentalizacao (como os 3 conceitos se conectam)
- Arquitetura minima (sensores/dados/modelo/atuacao)
- MVP de 30 dias (passos objetivos)
- KPI principal e KPI de risco
- Barreiras (tecnica, legal, adocao)
- Nivel de novidade (0-10) + justificativa

Contexto adicional:
- Perfil do executor: [SEU PERFIL]
- Recursos disponiveis: [TEMPO, EQUIPE, BUDGET, STACK]
- Restricoes: [PRIVACIDADE, LATENCIA, CUSTO, HARDWARE]
- Regiao-alvo: [PAIS/CIDADE/SETOR]

No final, entregue:
1) ranking das ideias por (impacto x viabilidade),
2) recomendacao da melhor primeira aposta,
3) plano de execucao em 3 sprints.
"""


