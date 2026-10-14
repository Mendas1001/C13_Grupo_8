# Projeto 1 – Identificação de Processos e Sintonia de PID (Grupo 8)

**Planta:** Cilindro pneumático
<<<<<<< HEAD
**Grupo:** 8
**Métodos de sintonia:** Técnica 4 (CHR com sobrevalor de 20%) e Técnica 5 (Cohen-Coon)
**Desempenho a avaliar:** menor tempo de resposta. Neste relatório, o critério principal é o tempo de acomodação (atingir e permanecer na banda de ±2%); o tempo de subida também é informado como métrica complementar.

## Executar a IHM (Integrante 3)

Na raiz desta pasta, no Windows:

1. Execute `iniciar_dashboard.bat`. Na primeira execução, o script cria o ambiente virtual local e instala as dependências.
2. Abra [http://127.0.0.1:8000](http://127.0.0.1:8000) no navegador. O arquivo `.mat` que acompanha o projeto é carregado automaticamente.
3. Use as abas **Visão geral**, **Identificação**, **Controle PID** e **Comparativo**. O grupo compara a **Técnica 4 — CHR com sobrevalor (20%)** com a **Técnica 5 — Cohen-Coon**. Em **Controle PID**, selecione o modelo, ajuste o SetPoint e clique em **Simular controle**; também há modo manual para Kp, Ti e Td.
4. Depois da simulação, use **Baixar dados** no cabeçalho para salvar em CSV as curvas de malha aberta/fechada e o SetPoint. Use **Salvar gráfico** na área da resposta temporal para baixar a figura em PNG. Para analisar outro ensaio, importe um arquivo `.mat` com as variáveis `t`, `Degrau` e `Saida`.

Para iniciar pelo terminal, na raiz do projeto:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn dashboard.server:app --host 127.0.0.1 --port 8000
```

Se a porta 8000 já estiver ocupada, feche o servidor anterior antes de iniciar outro. A interface e a API são executadas localmente; a simulação não controla o cilindro físico e não aplica limites de atuador.

Para validar a API e as funções do projeto:

```powershell
python -m pytest -q
```

O frontend fica em `dashboard/templates/index.html` e `dashboard/static/`; a API está em `dashboard/server.py`.
=======
**Métodos de sintonia:** Técnica 4 (CHR com Sobrevalor) e Técnica 5 (Cohen e Coon)
**Desempenho a avaliar:** (a) menor tempo de resposta
>>>>>>> origin/main

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

O arquivo contém os sinais `Degrau` (entrada) e `Saida` (saída), sem metadados que especifiquem a unidade física da entrada. No tratamento dos resultados do projeto, a saída é interpretada como pressão em bar; a entrada é mantida na unidade numérica fornecida pelo dataset.

| Item | Descrição e faixa observada |
|---|---|
| Variável controlada (PV) | `Saida`, interpretada como pressão: aproximadamente 1,1143 a 7,9969 bar no ensaio. |
| Variável manipulada (MV) | `Degrau`, entrada de 0 a 60 unidades do dataset. A unidade física não está identificada no arquivo; não se presume calibração em V ou mA. |
| Perturbações relevantes | Pressão de alimentação, carga, atrito, vazamentos e temperatura podem afetar um cilindro real. O ensaio fornecido não registra nem quantifica essas perturbações. |

Em uma implementação física, uma válvula proporcional pode atuar sobre o fluxo de ar e transdutores podem medir pressão ou posição. A seleção e a faixa desses instrumentos dependem da planta real e não podem ser inferidas apenas deste ensaio simulado.

## 2. Parte prática – Identificação (Integrante 1)

Script: [`Identificacao.py`](Identificacao.py)

1. Carrega o `Dataset Grupo8`, detecta o instante do degrau e calcula `k = Δy/Δu`.
2. Aplica **Smith** (28,3 % e 63,2 %) e **Sundaresan** (35,3 % e 85,3 %) e calcula `τ` e `θ`.
3. Calcula o **EQM/RMSE** de cada modelo contra o dataset e escolhe o menor.
4. Faz **ajuste fino** de `k, τ, θ` (Nelder-Mead) minimizando o EQM e gera a FT com Padé.

### Resultados do dataset fornecido

| Método | k | τ (s) | θ (s) | RMSE |
|---|---:|---:|---:|---:|
| Smith | 0,114711 | 54,738435 | 13,934558 | 0,218307 |
| Sundaresan | 0,114711 | 55,696968 | 14,693722 | 0,225653 |
| Ajuste fino | 0,114995 | 61,729994 | 8,592578 | 0,180319 |

O método Smith tem o menor RMSE entre os dois métodos clássicos pedidos, por isso é a identificação clássica escolhida para a comparação de sintonia. O ajuste fino opcional reduz ainda mais o RMSE, mas não é uma terceira técnica de sintonia do Grupo 8.

<<<<<<< HEAD
No ensaio, o degrau ocorre em 20 s, com `Degrau` variando de 0 para 60; a saída varia de aproximadamente 1,1143 para 7,9969 bar. O RMSE quantifica a diferença entre as amostras observadas e a resposta FOPDT estimada; Smith apresenta menor erro que Sundaresan neste conjunto específico.

## 3. Resultados integrados (itens 4, 5 e 6)

Resultados calculados para o modelo Smith, SetPoint de 8 bar, horizonte de 400 s e aproximação de Padé de 5ª ordem. O PID usa derivada filtrada (N=10). A malha aberta é calculada com o degrau equivalente para alcançar a mesma referência.

| Resposta | Subida 10–90% (s) | Acomodação ±2% (s) | Overshoot (%) | Erro final (bar) |
|---|---:|---:|---:|---:|
| Malha aberta equivalente | 120,273 | 228,2 | 0,000 | 0,00596 |
| Técnica 4 — CHR 20% | 20,622 | **94,4** | 20,491 | 0,00184 |
| Técnica 5 — Cohen–Coon | **17,452** | 163,2 | 78,236 | 0,00030 |

| Técnica | Kp | Ti (s) | Td (s) |
|---|---:|---:|---:|
| Técnica 4 — CHR com sobrevalor (20%) | 32,532568 | 74,280056 | 6,591046 |
| Técnica 5 — Cohen–Coon | 47,839138 | 31,070298 | 4,842957 |

**Conclusão para o critério do grupo:** adotando tempo de acomodação como tempo de resposta — pois mede quando a saída atinge e permanece próxima da referência — a Técnica 4 (CHR) é mais rápida: 94,4 s contra 163,2 s. A Técnica 5 (Cohen–Coon) tem menor tempo de subida (17,452 s contra 20,622 s), mas apresenta overshoot observado consideravelmente maior (78,236% contra 20,491%). Assim, a conclusão depende da métrica: CHR vence em acomodação; Cohen–Coon vence em subida.

Os parâmetros e gráficos refletem um modelo linear com atraso aproximado por Padé, sem saturação do atuador, limites físicos de pressão, anti-windup ou dinâmica detalhada da válvula. Os resultados são de simulação e não certificam estabilidade ou segurança de um cilindro físico.

As figuras salvas pelo script do Integrante 2 estão em `resultados2/`: `01_malha_aberta.png`, `02_pid_comparativo.png` e `03_malhas_comparacao.png`.
=======
**Análise da aproximação:** _(comentar a figura `resultados/identificacao_comparacao.png`)_
>>>>>>> origin/main
