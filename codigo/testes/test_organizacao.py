"""Protege os caminhos de saída e o contrato de montagem da reprodução."""
from pathlib import Path
import json
import unittest
from sistema.executar import BASE,validar_saida

class OrganizacaoTest(unittest.TestCase):
    def test_recusa_saida_em_dados_codigo_e_raiz(self):
        targets=[BASE,BASE.parent,BASE/'dados',BASE/'dados/fontes',BASE/'sistema',BASE/'experimentos/teste']
        if (BASE.parent/'.git').exists():targets.append(BASE.parent/'.git')
        for target in targets:
            with self.subTest(target=target),self.assertRaises(ValueError):validar_saida(target)

    def test_saida_padrao_permitida(self):
        self.assertEqual(validar_saida(BASE/'saidas'),(BASE/'saidas').resolve())

    def test_mapa_nao_reutiliza_csv_final_ou_metricas_calculadas(self):
        mapping=json.loads((BASE/'sistema/mapa_reproducao.json').read_text(encoding='utf-8'))
        destinations=[r['destino'] for r in mapping['arquivos']]
        self.assertEqual(len(destinations),len(set(destinations)))
        self.assertNotIn('publicacao.csv',destinations)
        self.assertNotIn('previsao.txt',destinations)
        self.assertFalse(any(d.startswith('dados/') for d in destinations))
        self.assertEqual({d for d in destinations if d.startswith('resultados/')},
                         {'resultados/congelamento_r1.json','resultados/politica_congelada.json'})
        for item in mapping['arquivos']:self.assertTrue((BASE/item['origem']).is_file())

if __name__=='__main__':unittest.main()
