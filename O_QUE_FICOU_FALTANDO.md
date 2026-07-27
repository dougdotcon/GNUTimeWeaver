# O Que Ficou Faltando

Este documento registra a diferença entre o MVP entregue e o GNU TimeWeaver
descrito no planejamento do sistema. O MVP está operacional, mas ele é uma
prova de armazenamento temporal local; ainda não é a implementação completa de
um debugger de agentes conectado à memória de um modelo de linguagem.

## Resumo honesto

| Área | Estado atual | Falta para cumprir a visão |
| --- | --- | --- |
| DAG e linhagem | Implementado em C | WAL, recuperação e compactação |
| Copy-on-Write | Implementado por páginas de arquivo | CoW de blocos KV reais e contagem de referências do runtime |
| `mmap` | Implementado para memória/arquivo CPU | Integração com alocações CUDA e VRAM |
| Fork e resume | Funciona no agente SQL demonstrativo | Continuar um agente local real a partir de um KV cache válido |
| Modelo | Simulador determinístico de demonstração | SML local carregado e executando inferência |
| Interface | Painel DAG, inspector e mutação de prompt | Breakpoints ao vivo, streaming de tokens e diff de contexto |
| Execução | Processo local único | Instrumentação de processos externos e pausa segura |
| Validação | Testes de CoW, persistência e integração CLI/API | Benchmarks GPU, falha de processo, fuzzing e modelos reais |
| Distribuição | Código-fonte + compilação local | Pacote instalável para GNU/Linux e documentação de integração |

## Lacunas críticas

### 1. Adaptador de inferência local

O agente atual (`src/native/demo_agent.c`) não carrega pesos nem gera tokens.
Ele simula uma trajetória de agente para validar o motor. Ainda falta uma ABI e
um adaptador funcional para pelo menos um runtime local, inicialmente vLLM ou
llama.cpp, que consiga:

- registrar início, pausa, erro, término e cursor de cada request;
- associar cada nó a prompt, sampler, seed, tokenizer, modelo e parâmetros;
- exportar e restaurar o estado necessário para continuar a geração;
- devolver eventos de bloco KV ao TimeWeaver sem enviar dados para a nuvem.

Sem esse adaptador, a ferramenta ainda não depura um modelo de linguagem real.

### 2. Snapshot do KV cache real

O MVP usa 16 páginas de memória com formato semelhante a blocos KV, mas são
bytes de demonstração em RAM/arquivo. Ainda falta mapear a representação real
de `K` e `V`, incluindo:

- layout por camada, cabeça, bloco, sequência e dtype;
- hash de bloco e hash do prefixo pai;
- referência compartilhada, evicção e expiração;
- compatibilidade entre versões de modelo, LoRA, RoPE, tokenizer e sampler;
- reconstrução de uma tabela de blocos aceita pelo runtime de inferência.

O contrato deve aproveitar os eventos e blocos expostos pelo vLLM, mas não pode
assumir que `mmap` de SSD seja remapeamento de VRAM.

### 3. CoW e hot-swap na GPU

O planejamento promete troca quase instantânea no espaço latente. Isso ainda
não existe no MVP. Faltam um backend CUDA, gerenciamento de memória residente,
sincronização de streams e uma política segura para:

1. manter blocos compartilhados somente para leitura;
2. duplicar um bloco quando uma continuação o modificar;
3. publicar a nova tabela de páginas sem corromper uma geração em andamento;
4. medir latência, VRAM usada e custo de cópia em hardware real.

Até essa etapa, qualquer alegação de `0 ms`, de manipulação direta de tensores
ou de economia de VRAM é uma hipótese, não um resultado deste repositório.

### 4. Pausa em tempo real e instrumentação

Hoje o fluxo é executado dentro do processo de demonstração. Falta um protocolo
para agentes externos e de longa duração:

- SDK Python e JavaScript para envolver uma etapa sem alterar o agente;
- canal local IPC (Unix socket ou equivalente) para eventos e comandos;
- pausa cooperativa em um ponto seguro do scheduler;
- timeout, cancelamento e retomada após queda do processo;
- controle de versão do contrato de eventos.

Sem isso, o usuário não consegue clicar em um erro de um agente já rodando e
recuperar seu contexto real.

### 5. Dependências semânticas de um fork

O demo sabe que alterar o prompt invalida a seleção de dialeto. Um agente
genérico precisa declarar ou descobrir quais estados dependem de cada entrada.
Ainda faltam:

- grafo de dependências entre prompt, ferramentas, memória e observações;
- política para reexecutar somente a fronteira afetada;
- preservação de seed e sampler para replay reproduzível;
- diff estruturado de mensagens, ferramentas, arquivos e resultados;
- sinalização clara de estados que não podem ser restaurados com segurança.

### 6. Durabilidade e operação de produção

O formato v1 é single-writer e tem capacidade fixa. Antes de uso contínuo,
precisa de:

- write-ahead log e recuperação após interrupção entre os dois `msync`;
- lock entre processos e detecção de writer abandonado;
- arenas segmentadas para estados maiores que 512 KiB;
- garbage collection, compactação e deduplicação por hash;
- quotas, backpressure e métricas de espaço;
- criptografia em repouso, redaction de segredos e validação de workspace não
  confiável.

## Lacunas de produto

- Breakpoints condicionais por etapa, ferramenta, token ou métrica.
- Timeline de execução ao vivo, logs de streaming e busca no DAG.
- Diff entre dois estados, incluindo mensagens e blocos KV, não apenas contagem
  de páginas.
- Rewind sem criar fork e histórico de HEADs nomeados.
- Exportação/importação de uma execução e compartilhamento reprodutível.
- Visualização de tokens, latência, custo, seed, VRAM e páginas compartilhadas.
- CLI de inspeção com comandos equivalentes ao `status`, `log`, `checkout`,
  `diff`, `fork` e `continue`.
- API pública estável, exemplos com agentes populares e política de versionamento.

## Lacunas de qualidade e segurança

- Testes de propriedade para qualquer sequência válida de snapshots e forks.
- Fuzzing do cabeçalho, dos nós e dos arquivos `graph.twm`/`pages.twd`.
- Testes de fault injection durante flush, queda e reabertura.
- Testes multi-processo e de concorrência no backend Linux.
- Testes com modelos reais, contextos longos, quantização e múltiplas sessões.
- Benchmark comparando replay completo, prefix caching e retomada TimeWeaver.
- Medição em GPU: tempo de fork, tokens por segundo, pico de VRAM e throughput.
- Revisão de segurança do IPC, isolamento de ferramentas e remoção de dados
  sensíveis antes da persistência.
- Cabeçalhos SPDX/copyright em todos os fontes e verificação das licenças dos
  runtimes e modelos que forem integrados.

## Ordem recomendada de execução

### P0 — provar a ponte com um modelo real

1. Escolher um runtime inicial (vLLM ou llama.cpp) e fixar sua versão.
2. Implementar o adaptador de eventos e o contrato de request/cursor.
3. Capturar um contexto real em CPU, criar um fork e continuar a geração.
4. Demonstrar que o prefixo não é tokenizado ou calculado novamente.
5. Medir replay completo versus fork em um benchmark reproduzível.

### P1 — tornar o núcleo confiável

1. WAL, recovery e lock de workspace.
2. Arenas segmentadas, GC e estados maiores que 512 KiB.
3. SDK de instrumentação e IPC local.
4. Testes de crash, fuzzing e concorrência.

### P2 — chegar ao objetivo de hardware

1. Backend CUDA para blocos KV residentes.
2. Tabela de páginas CoW integrada ao scheduler do runtime.
3. Fork sem cópia de prefixo na VRAM, com sincronização de streams.
4. Benchmark público com métricas de latência, VRAM e tokens por segundo.
5. Hot-swapping de adaptadores/pesos como projeto separado do debugger temporal.

## Critério para declarar a visão completa

A visão original só deve ser considerada implementada quando um modelo local
real, em uma máquina Linux, puder ser pausado em uma etapa, ter seu prompt ou
memória mutado, criar um fork, restaurar os blocos KV anteriores e continuar a
geração com medição independente de que o prefixo não foi reprocessado. O MVP
atual é a fundação verificável para esse teste; ele não deve ser apresentado
como se já tivesse atingido esse critério.
# Real-model bridge status

The next milestone is CPU llama.cpp checkpoint/restore/fork proof. Until a
pinned runtime and explicit `TIMEWEAVER_MODEL_PATH` are available, the formal
status is `ADAPTER_PROTOCOL_READY_NO_REAL_MODEL`.
