# Integrante 2 — Grupo 8: resultados dos itens 4, 5 e 6

Dataset: `Pneumatico_G8.mat`. O modelo clássico escolhido é **Smith**, com menor RMSE que Sundaresan. O ajuste fino opcional reduz adicionalmente o RMSE, mas os controladores do Grupo 8 são calculados a partir dos modelos clássicos.

Modelo Smith FOPDT: k=0.114711, τ=54.738 s, θ=13.935 s. O ensaio tem pressão inicial interpretada de 1.1143 bar, saída final de 7.9969 bar e entrada degrau de 0 para 60 unidades do dataset. SetPoint avaliado: 8 bar; horizonte: 400 s; Padé: 5ª ordem.

## Identificação

| Método | k | τ (s) | θ (s) | RMSE |
|---|---:|---:|---:|---:|
| Smith | 0.114711 | 54.738435 | 13.934558 | 0.218307 |
| Sundaresan | 0.114711 | 55.696968 | 14.693722 | 0.225653 |
| Ajuste fino | 0.114995 | 61.729994 | 8.592578 | 0.180319 |

Smith é selecionado entre as duas técnicas clássicas pelo menor RMSE. O ajuste fino não substitui essa escolha nas regras de sintonia; é uma otimização opcional do modelo.

## Item 4 — Malha aberta e fechada

A resposta em malha aberta usa o degrau equivalente Δu=(SetPoint−y0)/k, para que a planta alcance a mesma referência usada pela malha fechada. Essa entrada equivalente é uma comparação matemática, não uma afirmação de que o comando físico seja idêntico. O tempo de subida é medido entre 10–90%; o tempo de acomodação é o instante após o qual a resposta permanece na banda de ±2% do incremento.

| Indicador | Aberta equivalente | CHR 20% | Cohen–Coon |
|---|---:|---:|---:|
| Subida (s) | 120.273 | 20.622 | 17.452 |
| Acomodação (s) | 228.2 | 94.4 | 163.2 |
| Overshoot (%) | 0.0 | 20.491 | 78.236 |
| Erro na última amostra (bar) | 0.00596 | 0.00184 | 0.00030 |

## Itens 5 e 6 — Sintonias e desempenho

| Técnica | Kp | Ti (s) | Td (s) | Estável no modelo linear |
|---|---:|---:|---:|---|
| Técnica 4 — CHR com sobrevalor de 20% | 32.532568 | 74.280056 | 6.591046 | Sim |
| Técnica 5 — Cohen–Coon | 47.839138 | 31.070298 | 4.842957 | Sim |

Para o critério do Grupo 8, este relatório define “menor tempo de resposta” como menor tempo de acomodação: a resposta não apenas cruza a faixa de referência, mas permanece dentro dela. Com essa definição, CHR é a vencedora (94.4 s contra 163.2 s). Cohen–Coon tem menor tempo de subida (17.452 s contra 20.622 s), mas maior overshoot observado (78.236% contra 20.491%). A conclusão deve sempre explicitar a métrica; se “tempo de resposta” for interpretado apenas como tempo de subida, Cohen–Coon é o mais rápido.

O rótulo CHR 20% identifica o critério nominal da regra, não garante que o overshoot medido seja exatamente 20%.

## Hipóteses e limites

- O atraso da planta é aproximado por Padé na malha fechada; a malha aberta usa a resposta FOPDT analítica e o degrau equivalente descrito acima.
- Foi utilizado PID com derivada filtrada (N=10); os ganhos Kp, Ti e Td seguem as fórmulas do enunciado.
- A entrada do dataset vai de 0 a 60, mas o arquivo não informa sua unidade física. A saída é interpretada como pressão em bar no relatório.
- Não há saturação, anti-windup, dinâmica de válvula ou limite físico de pressão. Valores iniciais negativos que possam surgir na aproximação racional não são medições físicas.
- O erro final é medido no fim do horizonte simulado, não é o erro analítico em regime infinito.

## Figuras geradas

1. `01_malha_aberta.png`
2. `02_pid_comparativo.png`
3. `03_malhas_comparacao.png`
