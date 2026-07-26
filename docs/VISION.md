# Visão do projeto

O TimeWeaver é um projeto de software livre para depurar fluxos de agentes de IA de forma local, determinística e audível. A proposta central é transformar o estado de execução de um agente em um objeto versionável, permitindo que um desenvolvedor pause, inspecione, ramifique e retome um fluxo sem precisar reexecutar tudo do início.

## Problema

Ferramentas modernas de observabilidade mostram o que aconteceu em um fluxo de agente, mas normalmente não permitem recuperar ou modificar o estado intermediário de forma precisa. Quando um agente erra em um passo intermediário, a resposta comum é descartar o contexto e recomeçar do zero, gastando tempo e tokens.

O TimeWeaver tenta preencher essa lacuna com uma abordagem mais próxima de um debugger do que de um simples painel de logs.

## Proposta

O projeto organiza checkpoints de execução em um grafo acíclico dirigido (DAG), usa snapshots baseados em Copy-on-Write e armazena páginas imutáveis em um formato persistente acessível via mmap. A ideia é permitir:

- criar checkpoints a partir do estado de um agente;
- comparar versões de estado entre nós do grafo;
- ramificar a execução a partir de um ponto anterior;
- preservar o histórico sem duplicar toda a memória a cada nova versão.

## O que o projeto entrega hoje

O repositório atual já contém um MVP funcional para validar a base técnica do conceito:

- um motor nativo em C com armazenamento local e persistência;
- suporte a snapshots de páginas e cópia sob escrita;
- um fluxo de demo com agente local que falha em uma sintaxe e depois continua em uma branch corrigida;
- uma interface local de dashboard/CLI para explorar checkpoints e realizar forks;
- uma licença GPL-3.0-only, alinhada com a filosofia de soberania cognitiva e execução local.

## O que não é o foco do MVP

Este repositório não pretende, neste estágio, oferecer:

- hot-swapping de pesos em VRAM;
- integração direta com vLLM, llama.cpp ou outros motores de inferência;
- suporte a execução em GPU com remapeamento de páginas de memória de vídeo.

O MVP prova a base de armazenamento e ramificação de estado. A próxima etapa é conectar essa ABI a um adaptador real de cache KV ou a um motor de inferência local, mantendo o mesmo modelo de depuração temporal.

## Público-alvo

O TimeWeaver é voltado a desenvolvedores que constroem agentes autônomos, pipelines de decisão e fluxos complexos de IA localmente, especialmente aqueles que precisam de controle mais fino sobre o estado intermediário e sobre o comportamento de ramificação.

## Direção estratégica

A direção do projeto é simples: criar uma infraestrutura local, aberta e verificável para depurar agentes de IA como se fossem programas tradicionais, começando pela persistência e evolução do estado e avançando em direção a integrações mais sofisticadas com motores de inferência.

