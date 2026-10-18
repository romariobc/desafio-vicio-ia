import unittest
from preparar import BASE, carregar, csv_ler, limpar
from pipeline import (ler_r1,mesmo_ramo,comparar,resumo_comparacao,ajustar_calibrador,
                      selecionar_politica,decidir,validar,metricas,wilson,elegivel)

class PipelineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qs,cls.temas=carregar()
        cls.r1=ler_r1(cls.qs,cls.temas)
        cls.refs=csv_ler(BASE/'referencia/referencia_normalizada.csv')
        cls.cal=[h for h in cls.refs if h['particao']=='calibracao']

    def test_fontes_e_evidencias_integrais(self):
        self.assertEqual(len(self.qs),359)
        self.assertEqual(len(self.temas),375)
        self.assertNotIn('5078',self.temas)
        self.assertNotIn('5234',self.temas)
        self.assertEqual(len(self.r1),359)  # leitor valida ID e evidência literal de cada questão.

    def test_html_nao_cria_texto_de_script(self):
        self.assertEqual(limpar('A<br>B &amp; C<script>ignore</script>'),'A B & C')

    def test_ramo_transitivo_nao_confunde_irmaos(self):
        self.assertTrue(mesmo_ramo('5062','5203',self.temas))
        self.assertTrue(mesmo_ramo('5203','5199',self.temas))
        self.assertFalse(mesmo_ramo('4387','4388',self.temas))
        self.assertFalse(mesmo_ramo('5203','5202',self.temas))

    def test_extra_correto_nao_conserta_central_errado(self):
        r={**self.r1[0],'id':'X','tema_central_id':'4388','extras_ids':'4387'}
        h={'id':'X','particao':'calibracao','veredito':'concordo','tema_referencia_id':'4387','sugestao_antiga':'4387'}
        self.assertEqual(comparar([r],[h],self.temas)[0]['acerto_ramo'],0)

    def test_concordancia_humana_nao_valida_nova_sugestao(self):
        h=next(h for h in self.refs if h['id']=='Q0024')
        r=next(r for r in self.r1 if r['id']=='Q0024')
        self.assertEqual(h['tema_referencia_id'],'4387')
        self.assertEqual(comparar([r],[h],self.temas)[0]['acerto_ramo'],0)

    def test_discordancia_sem_correcao_nao_e_gold_inventado(self):
        h=next(h for h in self.refs if h['id']=='Q0053')
        r=next(r for r in self.r1 if r['id']=='Q0053')
        p=comparar([r],[h],self.temas)[0]
        self.assertIsNone(p['acerto_ramo'])
        self.assertTrue(p['repete_sugestao_rejeitada'])
        self.assertEqual(resumo_comparacao([p])['referencias_completas'],0)

    def test_particoes_sem_intersecao(self):
        a={h['id'] for h in self.cal};b={h['id'] for h in self.refs if h['particao']!='calibracao'}
        self.assertFalse(a&b)
        self.assertEqual(len(a|b),60)
        self.assertEqual(sum(bool(h['tema_referencia_id']) for h in self.refs),57)

    def test_calibrador_recusa_teste(self):
        with self.assertRaises(AssertionError):ajustar_calibrador(self.r1,self.refs,self.temas)

    def test_probabilidades_monotonicas_e_sem_inflacao_arbitraria(self):
        c=ajustar_calibrador(self.r1,self.cal,self.temas)
        p=[c['bins'][b]['probabilidade_calibrada'] for b in ('baixo','medio','alto')]
        self.assertEqual(p,sorted(p))
        for b in c['bins'].values():self.assertGreater(b['probabilidade_calibrada'],0);self.assertLess(b['probabilidade_calibrada'],1)

    def test_sem_evidencia_nao_inventa_precisao_nem_publica(self):
        c=ajustar_calibrador(self.r1,[],self.temas)
        p=selecionar_politica(self.r1,[],self.temas,c)
        self.assertIsNone(p['corte_escolhido'])
        out=decidir(self.r1,None,c)
        self.assertFalse(any(r['decisao']=='publicar' for r in out))
        self.assertIsNone(metricas(out,[],self.temas)['publicadas_na_referencia']['precisao_ramo'])

    def test_alertas_bloqueiam_publicacao_mesmo_com_score_alto(self):
        r={**self.r1[0],'score_bruto':.99,'alertas':'mosaico'}
        self.assertFalse(elegivel(r))
        self.assertEqual(decidir([r],.8)[0]['decisao'],'revisar')

    def test_tres_estados_reconciliam_e_contrato_final(self):
        rows=csv_ler(BASE/'publicacao.csv')
        self.assertEqual(len(rows),359)
        self.assertEqual(len({r['id'] for r in rows}),359)
        for r in rows:validar(r,self.temas)
        m=metricas(rows,self.refs,self.temas)
        self.assertAlmostEqual(m['cobertura']+m['abstencao_total'],1)
        self.assertAlmostEqual(m['abstencao_total'],m['fila_revisao']+m['exclusao'])

    def test_wilson_nao_garante_95_com_dezesseis_acertos(self):
        self.assertLess(wilson(16,16)[0],.95)
        self.assertIsNone(wilson(0,0))

if __name__=='__main__':unittest.main()
