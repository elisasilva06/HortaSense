
# HortaSense

**Plataforma IoT de Monitoramento Ambiental e Apoio à Irrigação de Hortas**

Projeto desenvolvido para a disciplina de Microcontroladores do curso de Engenharia da Computação da Universidade Estadual do Maranhão (UEMA).

## 1. Sobre o projeto

O HortaSense é uma plataforma IoT destinada ao monitoramento das condições ambientais de hortas domésticas, comunitárias, escolares e de pequenos produtores.

A solução utiliza um microcontrolador ESP32 para coletar e processar medições ambientais, identificar condições de umidade do solo e transmitir os dados para uma aplicação web.

O objetivo é auxiliar o acompanhamento das condições de cultivo e apoiar decisões relacionadas à irrigação.

O sistema não realiza irrigação automática.

### Funcionalidades

- Monitoramento da temperatura do ar.
- Monitoramento da umidade relativa do ar.
- Monitoramento da temperatura do solo.
- Monitoramento simulado da umidade do solo.
- Classificação automática da condição hídrica.
- Sinalização por LEDs.
- Transmissão de telemetria via MQTT.
- Recepção das mensagens com Python.
- Armazenamento das medições em SQLite.
- Dashboard web desenvolvido com Streamlit.
- Visualização de indicadores e gráficos históricos.
- Identificação de ausência de medições recentes.

## 2. Tecnologias utilizadas

| Tecnologia | Aplicação |
|---|---|
| ESP32 | Microcontrolador responsável pelas leituras e processamento |
| Arduino C++ | Programação do firmware |
| Wokwi | Simulação do circuito eletrônico |
| Wi-Fi | Conectividade do ESP32 |
| MQTT | Comunicação de telemetria |
| EMQX | Broker MQTT utilizado nos testes |
| Python | Desenvolvimento do receptor e da aplicação |
| Paho MQTT | Recepção das mensagens |
| SQLite | Armazenamento local das medições |
| Streamlit | Interface web |
| Plotly | Visualização gráfica |
| Pandas | Organização e análise dos dados |

## 3. Hardware e simulação

O circuito é desenvolvido e testado no Wokwi.

### Componentes

| Componente | Função |
|---|---|
| ESP32 | Processamento e comunicação |
| DHT22 | Temperatura e umidade do ar |
| DS18B20 | Temperatura do solo |
| Potenciômetro | Simulação da umidade do solo |
| LED verde | Umidade adequada |
| LED amarelo | Atenção hídrica |
| LED vermelho | Necessidade de irrigação |

### Conexões utilizadas

| Componente | GPIO |
|---|---|
| DHT22 | 15 |
| DS18B20 | 12 |
| Potenciômetro | 34 |
| LED verde | 18 |
| LED amarelo | 19 |
| LED vermelho | 21 |

O potenciômetro representa a entrada analógica de um sensor de umidade do solo. Ele não realiza uma medição física de umidade.

### Link da simulação

Adicionar aqui o link compartilhável do projeto Wokwi:

`LINK_DO_PROJETO_WOKWI`

## 4. Funcionamento do sistema

O fluxo de processamento e comunicação é:

```text
Sensores simulados
       |
       v
      ESP32
       |
       | Wi-Fi / MQTT
       v
   Broker EMQX
       |
       | Assinatura MQTT
       v
 Receptor Python
       |
       v
  Banco SQLite
       |
       v
Dashboard Streamlit
```

O ESP32 realiza a aquisição e a classificação das medições.

As informações são publicadas em um tópico MQTT e recebidas pelo programa `mqtt_receiver.py`.

O receptor armazena os registros no SQLite.

O dashboard consulta o banco e apresenta as informações ao usuário.

## 5. Classificação da umidade do solo

O ESP32 utiliza os seguintes limites iniciais:

| Umidade | Condição | Sinalização |
|---|---|---|
| Até 30% | Necessidade de irrigação | LED vermelho |
| Acima de 30% até 50% | Atenção hídrica | LED amarelo |
| Acima de 50% | Umidade adequada | LED verde |

Os limites são parâmetros definidos para testes do protótipo e não representam recomendações universais de irrigação.

Na simulação, a conversão da entrada analógica utiliza as referências ADC 4000 para solo seco e 500 para solo úmido.

## 6. Comunicação MQTT

Configuração utilizada no ambiente de desenvolvimento:

```text
Broker: broker.emqx.io
Porta: 1883
Tópico: hortasense/grupo01/estufa01/telemetria
Intervalo de publicação: aproximadamente 5 segundos
Formato: JSON
```

Exemplo de mensagem:

```json
{
  "device": "hortasense_01",
  "air_temperature_c": 24.0,
  "air_humidity_pct": 40.0,
  "soil_temperature_c": 22.0,
  "soil_moisture_pct": 60,
  "soil_adc": 1897,
  "irrigation_status": "UMIDADE_ADEQUADA",
  "uptime_ms": 85760
}
```

O broker utilizado é público e a conexão experimental na porta 1883 não utiliza TLS.

Não enviar informações pessoais ou credenciais por esse tópico.

Para evitar conflitos durante testes simultâneos, cada integrante deverá utilizar um identificador de dispositivo, tópico MQTT e identificador de cliente próprios, mantendo a configuração do publicador e do receptor compatíveis.

## 7. Estrutura do projeto

```text
hortasense/
│
├── .streamlit/
│   └── config.toml
│
├── components/
│   ├── __init__.py
│   ├── cards.py
│   ├── charts.py
│   └── layout.py
│
├── data/
│   └── .gitkeep
│
├── pages/
│   ├── __init__.py
│   ├── visao_geral.py
│   ├── historico.py
│   ├── alertas.py
│   └── configuracoes.py
│
├── services/
│   ├── __init__.py
│   └── indicators.py
│
├── app.py
├── database.py
├── mqtt_receiver.py
├── requirements.txt
├── README.md
└── .gitignore
```

O arquivo `data/hortasense.db` é gerado localmente e não deve ser versionado.

Os arquivos de firmware e simulação Wokwi deverão ser adicionados ao repositório quando estiverem organizados para compartilhamento.

## 8. Requisitos para execução

Antes de iniciar, instalar:

- Git.
- Python 3.12.
- Visual Studio Code ou outro editor.
- Navegador atualizado.
- Acesso à internet para o MQTT e o Wokwi.

As dependências Python estão definidas em `requirements.txt`.

## 9. Como clonar e executar

### 9.1. Clonar o repositório

No terminal:

```powershell
git clone URL_DO_REPOSITORIO
cd HortaSense
```

Substituir `URL_DO_REPOSITORIO` pelo endereço HTTPS do repositório.

### 9.2. Criar o ambiente virtual

No PowerShell:

```powershell
py -3.12 -m venv .venv
```

### 9.3. Ativar o ambiente virtual

```powershell
.\.venv\Scripts\Activate.ps1
```

Caso o PowerShell bloqueie a execução, verificar a política de execução do terminal antes de modificá-la.

### 9.4. Instalar as dependências

```powershell
python -m pip install -r requirements.txt
```

### 9.5. Iniciar o receptor MQTT

No primeiro terminal:

```powershell
python mqtt_receiver.py
```

Manter esse terminal em execução.

O receptor inicializa o banco de dados, quando necessário, e recebe as mensagens MQTT.

### 9.6. Iniciar o dashboard

Abrir um segundo terminal, ativar o ambiente virtual e executar:

```powershell
python -m streamlit run app.py
```

A interface estará disponível normalmente em:

http://localhost:8501

### 9.7. Iniciar a simulação Wokwi

Abrir o projeto compartilhado no Wokwi e iniciar a simulação.

Verificar no Serial Monitor:

- Conexão Wi-Fi.
- Conexão MQTT.
- Publicação das mensagens JSON.

Para receber novas medições, o receptor Python deve estar em execução e inscrito no mesmo tópico MQTT utilizado no firmware.

## 10. Páginas do dashboard

### Visão Geral

Apresenta:

- Indicadores ambientais.
- Condição hídrica.
- Horário da última medição.
- Verificação de dados recentes.
- Gráfico de umidade do solo.

### Histórico e Irrigação

Funcionalidades planejadas ou em desenvolvimento:

- Filtros por período.
- Médias, valores mínimos e máximos.
- Análise de variação.
- Comparação entre temperaturas.
- Histórico de medições.
- Registros manuais de irrigação.

### Alertas e Ocorrências

Funcionalidades previstas:

- Registro de condições críticas.
- Histórico das mudanças de classificação.
- Identificação de interrupções de telemetria.

### Configurações e Dispositivo

Funcionalidades previstas:

- Informações do dispositivo.
- Configuração dos parâmetros hídricos.
- Envio de comandos remotos.
- Consulta do estado de comunicação.

A existência da página na navegação não significa que todas as funcionalidades estejam implementadas.

## 11. Estado atual do desenvolvimento

### Implementado e testado

- Simulação do ESP32 e dos sensores.
- Aquisição das leituras.
- Conversão simulada da umidade do solo.
- Classificação das condições hídricas.
- Conexão Wi-Fi no Wokwi.
- Publicação MQTT.
- Recepção das mensagens pelo Python.
- Armazenamento das medições no SQLite.
- Página Visão Geral do dashboard.
- Indicadores ambientais e gráfico de umidade.

### Em desenvolvimento

- Análises estatísticas e gráficos avançados.
- Histórico completo e filtros por período.
- Registro manual de irrigação.
- Histórico de alertas e ocorrências.
- Configurações remotas.
- Recebimento de comandos MQTT pelo firmware.
- Testes adicionais de integração.

## 12. Testes

Para validar a integração:

1. Iniciar o Wokwi.
2. Confirmar a publicação MQTT no Serial Monitor.
3. Iniciar o receptor Python.
4. Confirmar o recebimento das mensagens.
5. Verificar a criação e a atualização do SQLite.
6. Iniciar o dashboard.
7. Conferir os indicadores e o histórico.
8. Alterar o potenciômetro e observar as novas medições.

O recebimento MQTT e a atualização visual são processos distintos. Se o dashboard não apresentar novos dados, verificar primeiro se o receptor está armazenando novas medições.

## 13. Colaboração pelo GitHub

Cada integrante deverá trabalhar preferencialmente em uma branch própria.

Criar uma branch:

```powershell
git switch -c feature/nome-da-funcionalidade
```

Registrar alterações:

```powershell
git add .
git commit -m "feat: descricao da funcionalidade"
```

Enviar a branch:

```powershell
git push -u origin feature/nome-da-funcionalidade
```

Depois, abrir um Pull Request para revisão antes de incorporar as mudanças à branch principal.

Não enviar para o GitHub:

- Ambiente virtual `.venv`.
- Banco SQLite com medições locais.
- Arquivos temporários.
- Credenciais e tokens.
- Configurações privadas.
- Arquivos gerados durante a execução.

## 14. Limitações

O projeto utiliza um ambiente de simulação.

As medições do potenciômetro não equivalem à validação de um sensor físico calibrado.

O SQLite está configurado para uso local.

A comunicação MQTT utiliza um broker público de testes.

O protótipo ainda não possui todos os recursos necessários para uma implantação contínua em produção.

## 15. Contexto acadêmico

O HortaSense é desenvolvido como projeto acadêmico da disciplina de Microcontroladores.

Na P2, o foco é a implementação e a validação técnica do sistema.

A análise comercial, a proposta de valor e a apresentação de negócio serão tratadas na P3.

---

**HortaSense — Engenharia da Computação | UEMA**
