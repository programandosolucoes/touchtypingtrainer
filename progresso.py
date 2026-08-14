"""Lê o histórico e responde três perguntas, sem tocar em tela.

1. Estou melhorando? (`evolucao_por_dia`)
2. Que teclas eu mais erro? (`ranking_de_teclas`)
3. Que dedo é o culpado? (`ranking_de_dedos`)

Tudo aqui é leitura pura sobre a lista que o `historico.ler` devolve — o que
permite testar o diagnóstico inteiro sem abrir janela e sem gravar nada.
"""
import layouts

# Abaixo disso a amostra é pequena demais para acusar uma tecla: uma errada em
# duas tentativas viraria 50% de erro e lideraria o ranking sem significar nada.
MINIMO_DE_COBRANCAS = 5


def _por_data(registro):
    """A parte da data do carimbo ISO, ou None se o registro for velho demais."""
    quando = registro.get('quando')
    return quando[:10] if isinstance(quando, str) and len(quando) >= 10 else None


def evolucao_por_dia(registros, modo=None):
    """Um resumo por dia, em ordem crescente de data.

    Devolve lista de dicionários:
    `{'data': '2026-08-14', 'exercicios': 3, 'wpm_medio': 21.4,
      'precisao': 97.2, 'melhor_wpm': 24.0}`

    `precisao` é 100 − tropeços/teclas: no Modo Lição os erros do texto final são
    sempre zero (a trava impede), então tropeço é a única medida de qualidade.
    """
    dias = {}
    for registro in registros:
        if modo and registro.get('modo') != modo:
            continue
        data = _por_data(registro)
        if not data:
            continue
        dia = dias.setdefault(data, {'data': data, 'exercicios': 0, '_wpm': [],
                                     '_tropecos': 0, '_teclas': 0})
        dia['exercicios'] += 1
        wpm = registro.get('wpm_bruto')
        if isinstance(wpm, (int, float)):
            dia['_wpm'].append(float(wpm))
        dia['_tropecos'] += registro.get('tropecos') or 0
        dia['_teclas'] += registro.get('total_teclas') or 0
    resultado = []
    for data in sorted(dias):
        dia = dias[data]
        wpms = dia.pop('_wpm')
        tropecos, teclas = dia.pop('_tropecos'), dia.pop('_teclas')
        dia['wpm_medio'] = round(sum(wpms) / len(wpms), 1) if wpms else 0.0
        dia['melhor_wpm'] = round(max(wpms), 1) if wpms else 0.0
        dia['precisao'] = round(100 - (tropecos / teclas * 100), 1) if teclas else 100.0
        resultado.append(dia)
    return resultado


def esta_melhorando(evolucao, dias=5):
    """Compara a média de WPM dos últimos `dias` com a dos anteriores.

    Devolve a diferença em WPM, ou None quando não há dias suficientes dos dois
    lados para comparar — dizer "você piorou" com dois dias de dado seria mentira.
    """
    if len(evolucao) < 2:
        return None
    recentes = evolucao[-dias:]
    anteriores = evolucao[:-dias] or evolucao[:-1]
    if not anteriores or not recentes:
        return None
    media = lambda grupo: sum(d['wpm_medio'] for d in grupo) / len(grupo)  # noqa: E731
    return round(media(recentes) - media(anteriores), 1)


def _acumular_teclas(registros):
    total = {}
    for registro in registros:
        for tecla, dados in (registro.get('teclas') or {}).items():
            entrada = total.setdefault(tecla, {'acertos': 0, 'erros': 0,
                                               'ms_soma': 0.0, 'confusoes': {}})
            acertos = dados.get('acertos', 0)
            erros = dados.get('erros', 0)
            entrada['acertos'] += acertos
            entrada['erros'] += erros
            entrada['ms_soma'] += (dados.get('ms_medio') or 0) * (acertos + erros)
            for digitada, vezes in (dados.get('confusoes') or {}).items():
                entrada['confusoes'][digitada] = \
                    entrada['confusoes'].get(digitada, 0) + vezes
    return total


def ranking_de_teclas(registros, minimo=MINIMO_DE_COBRANCAS):
    """As teclas com mais erro, da pior para a melhor.

    Cada item: `{'tecla': 'j', 'cobrancas': 40, 'erros': 6, 'taxa': 15.0,
                 'ms_medio': 310, 'confusao': ('k', 4)}`

    `confusao` é a troca mais frequente — `('k', 4)` significa "digitou k no
    lugar de j, 4 vezes". É ela que revela dedo errado, não o erro em si.
    """
    ranking = []
    for tecla, dados in _acumular_teclas(registros).items():
        cobrancas = dados['acertos'] + dados['erros']
        if cobrancas < minimo:
            continue
        confusoes = dados['confusoes']
        pior = max(confusoes.items(), key=lambda par: par[1]) if confusoes else None
        ranking.append({
            'tecla': tecla,
            'cobrancas': cobrancas,
            'erros': dados['erros'],
            'taxa': round(dados['erros'] / cobrancas * 100, 1),
            'ms_medio': round(dados['ms_soma'] / cobrancas) if cobrancas else 0,
            'confusao': pior,
        })
    ranking.sort(key=lambda item: (-item['taxa'], -item['erros'], item['tecla']))
    return ranking


def ranking_de_dedos(registros, nome_layout):
    """Agrupa os erros por (mão, dedo), da pior combinação para a melhor.

    Cada item: `{'mao': 'direita', 'dedo': 'indicador', 'cobrancas': 120,
                 'erros': 14, 'taxa': 11.7}`
    """
    por_dedo = {}
    for tecla, dados in _acumular_teclas(registros).items():
        par = layouts.dedo_de(tecla, nome_layout)
        if not par:
            continue
        entrada = por_dedo.setdefault(par, {'cobrancas': 0, 'erros': 0})
        entrada['cobrancas'] += dados['acertos'] + dados['erros']
        entrada['erros'] += dados['erros']
    ranking = [{'mao': mao, 'dedo': dedo, 'cobrancas': v['cobrancas'],
                'erros': v['erros'],
                'taxa': round(v['erros'] / v['cobrancas'] * 100, 1) if v['cobrancas'] else 0.0}
               for (mao, dedo), v in por_dedo.items()]
    ranking.sort(key=lambda item: (-item['taxa'], -item['erros']))
    return ranking


def teclas_para_treinar(registros, quantas=6, minimo=MINIMO_DE_COBRANCAS):
    """As piores teclas, como conjunto pronto para gerar um treino dirigido."""
    return tuple(item['tecla'] for item in ranking_de_teclas(registros, minimo)
                 if item['erros'] > 0)[:quantas]


def resumo(registros, nome_layout):
    """Tudo de uma vez, para a tela não ter de orquestrar quatro chamadas."""
    evolucao = evolucao_por_dia(registros)
    return {
        'exercicios': len(registros),
        'dias': len(evolucao),
        'evolucao': evolucao,
        'tendencia': esta_melhorando(evolucao),
        'teclas': ranking_de_teclas(registros),
        'dedos': ranking_de_dedos(registros, nome_layout),
        'para_treinar': teclas_para_treinar(registros),
    }
