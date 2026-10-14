# Projeto 1 – Identificação de Processos e Sintonia de PID (Grupo 8)

**Planta:** Cilindro pneumático
**Métodos de sintonia:** Técnica 4 (CHR com Sobrevalor) e Técnica 5 (Cohen e Coon)
**Desempenho a avaliar:** (a) menor tempo de resposta

## 1. Parte teórica

### 1.1 Funcionamento da planta

O cilindro pneumático converte a energia do ar comprimido em movimento linear. O ar, fornecido por um
compressor e condicionado por uma unidade de tratamento (filtro, regulador de pressão e lubrificador),
chega a uma válvula direcional, que o direciona a uma das câmaras do cilindro. A diferença de pressão
entre as câmaras gera uma força sobre o êmbolo que, descontados o atrito e a carga, desloca a haste.
Em um posicionamento controlado, usa-se uma válvula proporcional (ou servoválvula), cuja abertura
define a vazão de ar em cada câmara e, portanto, a velocidade e a posição do êmbolo.

Por causa da compressibilidade do ar, do volume das câmaras e das tubulações, e do atrito
(*stick-slip*), a resposta é lenta e apresenta atraso: a pressão precisa se acumular antes que o êmbolo
se mova. Isso justifica a modelagem como sistema de primeira ordem com atraso de transporte (FOPDT):

$$H(s)=\frac{k}{\tau s+1}e^{-\theta s}$$

### 1.2 Sensores e atuadores para um controlador real

| Tipo | Opções |
|---|---|
| Sensores de posição | Potenciômetro linear, transdutor magnetostritivo, LVDT, encoder linear/óptico, sensor de distância a laser |
| Sensores de pressão | Transdutores de pressão (0–10 bar) nas câmaras e na linha de alimentação |
| Sensores de fim de curso | Reed switch (sensor magnético no êmbolo), sensores indutivos |
| Atuadores | Válvula proporcional de vazão ou direcional proporcional (comando 0–10 V ou 4–20 mA), servoválvula; cilindro de dupla ação |
| Controlador | Microcontrolador/CLP com ADC/DAC ou saída PWM, rodando o algoritmo PID |

### 1.3 Variáveis do processo

> **Atenção:** confirmar com o dataset do Grupo 8 qual é a grandeza de saída (posição, pressão,
> velocidade) e as unidades, e ajustar a tabela abaixo. As faixas são valores típicos.

| Item | Descrição | Faixa típica |
|---|---|---|
| Variável controlada (PV) | Posição do êmbolo/haste (ou grandeza do dataset) | 0 a curso útil (ex.: 0–200 mm) |
| Variável manipulada (MV) | Abertura da válvula proporcional (tensão/corrente de comando) | 0–10 V ou 4–20 mA (0–100 %) |
| Perturbação 1 | Variação da pressão de alimentação | 4 a 8 bar (nominal ~6 bar) |
| Perturbação 2 | Variação da carga/massa acoplada e forças externas | Depende da aplicação (0 a carga nominal do cilindro) |
| Perturbação 3 | Atrito (*stick-slip*), desgaste das vedações, lubrificação | Variável no tempo |
| Perturbação 4 | Vazamentos e temperatura do ar (alteram a compressibilidade) | Temperatura ambiente típica 5–40 °C |

## 2. Parte prática – Identificação (Integrante 1)

Script: [`identificacao.py`](identificacao.py)

1. Carrega o `Dataset Grupo8`, detecta o instante do degrau e calcula `k = Δy/Δu`.
2. Aplica **Smith** (28,3 % e 63,2 %) e **Sundaresan** (35,3 % e 85,3 %) e calcula `τ` e `θ`.
3. Calcula o **EQM/RMSE** de cada modelo contra o dataset e escolhe o menor.
4. Faz **ajuste fino** de `k, τ, θ` (Nelder-Mead) minimizando o EQM e gera a FT com Padé.

### Resultados (preencher após rodar o script)

| Método | k | τ | θ | EQM |
|---|---|---|---|---|
| Smith | | | | |
| Sundaresan | | | | |
| Ajuste fino | | | | |

**Método escolhido e justificativa:** _(preencher: menor EQM; Sundaresan é mais robusto a ruído por
não depender de tangente, Smith é adequado para curvas limpas)_

**Análise da aproximação:** _(comentar a figura `resultados/identificacao_comparacao.png`)_
