# -*- coding: utf-8 -*-

import time
import urllib
import re
import operator
import json
import itertools
import progressbar
from joblib import Parallel, delayed
import multiprocessing

meses = zip(["janeiro","fevereiro","março","abril","maio","junho","julho","agosto","setembro","outubro","novembro","dezembro"],range(1,13))

def chunkify(a, n):
 k, m = divmod(len(a), n)
 return (a[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in xrange(n))


def CleanHTML(text):
 cleanr = re.compile('<.*?>')
 cleantext = re.sub(cleanr, '', text)
 regex = re.compile(r'[\n\r\t]')
 regex.sub(' ', cleantext)
 return cleantext

def is_float(value):
 try:
  float(value)
  return True
 except:
  return False

def _getIDs (page):
 url = "http://www.portaltransparencia.gov.br/servidores/OrgaoLotacao-ListaServidores.asp?CodOrg=26235&Pagina="+str(page)
 f = urllib.urlopen(url).read().decode("ISO-8859-1")
 raw = [y[y.index("IdServidor=")+len("IdServidor="):y.index("&")].decode("latin-1") for y in [x for x in f[f.find("<td class=\"firstChild\">"):f.find("<noscript> </noscript>")].split("\n") if "IdServidor=" in x]]
 return raw

def getDados (dados):
 dados = [x.rstrip() for x in CleanHTML(dados[dados.index("<tr class=\""):dados.index("<div id=\"saibamais\">")]).replace("&nbsp;","").split("  ")]
 dados = filter(None, dados)
 dados = filter(None, dados)
 dados = [elem.replace(".","").replace(",",".").replace("\n","").replace("\r","").replace("\t","").rstrip() for elem in dados]

 s = {}
 dictAtual = None
 for i in range(0,len(dados)):
  if ":" in dados[i]:
   dictAtual = dados[i].split(":")[0].strip()
   s[dictAtual] = dados[i].split(":")[1].strip()
  if i>0:
   if not is_float(dados[i]) and not is_float(dados[i-1]):
    dictAtual = dados[i-1]
    s[dictAtual] = {}
   elif is_float(dados[i]) and not is_float(dados[i-1]):
     s[dictAtual][dados[i-1]] = dados[i] 

 dados = s
 return dados

def getSalario (url):
 f = urllib.urlopen(url).read().decode("ISO-8859-1")
 periodos = [x.strip() for x in CleanHTML(f[f.index("<div id=\"navegacaomeses\">"):f.index("<div id=\"listagemConvenios\">")]).split("\n") if "|" not in x]
 periodos = filter(None, periodos)
 periodos = [tuple(x.lower().split("/")) for x in periodos]
 urls = []
 for i in range(0,len(periodos)):
  periodos[i] = (str((meses[[x[0].decode('utf-8') for x in meses].index(periodos[i][0].decode('utf-8'))][1])),periodos[i][1])
  urls.append(url+"&Ano="+periodos[i][1]+"&Mes="+periodos[i][0])

 s = {}
 for elemento in zip(urls,periodos):
  paginaPeriodo = urllib.urlopen(elemento[0]).read().decode("ISO-8859-1")
  s["_".join(list(elemento[1]))] = getDados(paginaPeriodo)
 return s
  

def _getByID (id):
 url = "http://www.portaltransparencia.gov.br/servidores/OrgaoLotacao-DetalhaServidor.asp?IdServidor="+str(id)+"&CodOrgao=26235"
 f = urllib.urlopen(url).read().decode("ISO-8859-1")
 aux = f

 if "InformacaoFinanceira=True" not in aux:
  salario = None
 else:
  urlSalario = "http://www.portaltransparencia.gov.br" + aux[aux.index("/servidores/Servidor-DetalhaRemuneracao.asp?"):aux.index("InformacaoFinanceira=True\"")+len("InformacaoFinanceira=True")]
  salario = getSalario(urlSalario)

 fs = f[f.index("<!-- cabecalho da tabela -->"):f.index("<div id=\"saibamais\">")].split("<!-- cabecalho da tabela -->")[1:]
 ss = []
 for f in fs:
  f = f.split("\n")
  f = [CleanHTML(f[i]).strip().replace(":","")+":"+CleanHTML(f[i+1]).strip() for i in range(0,len(f)) if "tituloDetalhe" in f[i]]
  s = {}
  dictAtual = None

  for i in range(0,len(f)):
   if "&nbsp; &nbsp;" not in f[i]:
    dictAtual = f[i].split(":")[0]
    s[dictAtual] = [f[i].split(":")[1],{}]
   if "&nbsp; &nbsp;" in f[i]:
    s[dictAtual][1][f[i].split(":")[0]] = " ".join(f[i].split(":")[1:]).replace("&nbsp; &nbsp;","")
  ss.append(s)
 
 ss =  zip([(x[0]+" "+str(x[1])) for x in list(itertools.product(["Cargo"],range(0,10)))],ss)
 ss = dict(ss)
 aux = CleanHTML(aux[aux.index("<table summary=\"Identifica"):aux.index("\"listagemConvenios\"")]).replace("\r","").replace("\t","").rstrip().split("\n")
 aux = filter(None, [x.strip() for x in aux])[3:-1]

 aux = dict(zip(aux[::2], aux[1::2]))
 ss['dados_gerais'] = aux
 return {"ID":id,"Info":{'dados_funcionais':ss,'financeiro':salario}}

def getQtdePaginas ():
 url = "http://www.portaltransparencia.gov.br/servidores/OrgaoLotacao-ListaServidores.asp?CodOrg=26235&Pagina=1"
 f = int([CleanHTML(x).split("/")[1].rstrip() for x in urllib.urlopen(url).read().decode("ISO-8859-1").split("\n") if "<p class=\"paginaAtual\">" in x][0])
 return f

def main():
 #s = _getByID(1187673)
 #with open('saida.json', 'w') as outfile:
  #json.dump(s, outfile)

 num_cores = 8#multiprocessing.cpu_count()
 nPaginas = getQtdePaginas()

 cont = 54
 nPedacos = 62
 t_0 = time.time()
 for k in chunkify(range(54,nPaginas),nPedacos):#a cada k paginas, grave em arquivo, cada pagina tem 15 entradas
  start_time = time.time()
  print("[MSG] Processando parte " + str(cont) + " de " + str(nPedacos) + " -> [" + str(k[0]) + "," + str(k[len(k)-1]) + "]")
  s = []
  s = Parallel(n_jobs=num_cores,verbose=5)(delayed(_getByID)(elemento) for elemento in reduce(operator.concat, [_getIDs(i+1) for i in range(k[0],k[len(k)-1])]))
  print("[MSG] Realizando gravação")
  for pessoa in s:
   with open(pessoa["ID"]+'.json', 'w') as outfile:
    json.dump(pessoa, outfile)
  elapsed_time = time.time() - start_time
  print("[MSG] Parte " + str(cont) + " de " + str(nPedacos) + " processada -> Tempo gasto = " +  str(elapsed_time) + " s")
  print("[MSG] Tempo gasto total = " + str(time.time()-t_0))
  cont += 1

if __name__ == '__main__':
 main()
