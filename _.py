from progressbar import ProgressBar
import urllib
import os
import sys
import re

def cleanhtml(raw_html):
  cleanr = re.compile('<.*?>')
  cleantext = re.sub(cleanr, '', raw_html)
  return cleantext

def ValidaCpf(cpf,d1=0,d2=0,i=0):
 while i<10:
  d1,d2,i=(d1+(int(cpf[i])*(11-i-1)))%11 if i<9 else d1,(d2+(int(cpf[i])*(11-i)))%11,i+1
 return (int(cpf[9])==(11-d1 if d1>1 else 0)) and (int(cpf[10])==(11-d2 if d2>1 else 0))

def GeraCPFs (cpf):
 listaCPFs = []
 cpf = cpf.replace("***.","").replace("-**","").replace(".","")
 for primeiroCampo in range(0,1000):
  for ultimoCampo in range(0,100):   
   str1 = str(primeiroCampo)
   str2 = str(ultimoCampo)
   str1 = str1 if primeiroCampo>=100 else ("0" + str1 if primeiroCampo>=10 else "00" + str1)
   str2 = str2 if ultimoCampo>=10 else "0" + str2
   if(ValidaCpf(str(str1+cpf+str2))):
    listaCPFs.append(str(str1+cpf+str2))
 return listaCPFs

def DecodificaCPF(cpf,nome):
 possiveisCPFs = GeraCPFs(cpf)
 i = 0
 print("Decodificando CPF = " + cpf)
 pbar = ProgressBar()
 for cpf in pbar(possiveisCPFs):
  url = "http://transparencia.gov.br/servidores/Servidor-ListaServidores.asp?bogus=1&Pagina=1&TextoPesquisa="+cpf
  f = urllib.urlopen(url).read().decode("ISO-8859-1")
  if "IdServidor" in f and nome in f:
   print cpf
   return cpf
  i = i+1
 return -1

def getQtdePaginas (nome):
 entrada = []
 tagsParaExclusao = ["</div>","</table>","</tr>","<tr >","<td class=\"firstChild\">","</td>","</a>","<td style=\"text-align: left;\">","<td style=\"text-align: right;\">","<tr  class=\"linhaPar\" >","<td><a href=\"Servidor-DetalhaServidor.asp?IdServidor=","<script type=\"text/javascript\" language=\"javascript\" src=\"../../Recursos/helper.js\"></script>"]
 url = "http://transparencia.gov.br/servidores/Servidor-ListaServidores.asp?bogus=1&Pagina=1&TextoPesquisa="+nome
 f = urllib.urlopen(url).read().decode("ISO-8859-1")
 nPaginas = f[f.find("<p class=\"paginaAtual\">")+len("<p class=\"paginaAtual\">"):]
 nPaginaFinal = nPaginas[7:nPaginas.find("</p>")].split("/")[1]
 nPaginaFinal = int(nPaginaFinal)
 return nPaginaFinal

def getResultadosPorPagina (nome,pagina,permiteDecodificacao):
 entrada = []
 tagsParaExclusao = ["</div>","</table>","</tr>","<tr >","<td class=\"firstChild\">","</td>","</a>","<td style=\"text-align: left;\">","<td style=\"text-align: right;\">","<tr  class=\"linhaPar\" >","<td><a href=\"Servidor-DetalhaServidor.asp?IdServidor=","<script type=\"text/javascript\" language=\"javascript\" src=\"../../Recursos/helper.js\"></script>"]

 url = "http://transparencia.gov.br/servidores/Servidor-ListaServidores.asp?bogus=1&Pagina="+str(pagina)+"&TextoPesquisa="+nome
 f = urllib.urlopen(url).read().decode("ISO-8859-1")

 raw = f[f.find("<td class=\"firstChild\">"):f.find("<noscript> </noscript>")]
 raw = cleanhtml(raw) 
 raw = raw.splitlines()
 
 resultados = []
 i=0
 while(i<len(raw)-12):
  cpf = raw[i].strip()
  if(permiteDecodificacao==1):
   cpf = DecodificaCPF(cpf,nome) 
  nome = raw[i+1][raw[i+1].find("\">")+2:].strip(' ')
  orgaoLotacao = raw[i+2].strip(' ')
  orgaoExercicio = raw[i+3].strip(' ')
  it = {'cpf':cpf,'nome':nome,'orgaoLotacao':orgaoLotacao,'orgaoExercicio':orgaoExercicio}
  #print(it)
  resultados.append(it)
  i += 12 
 return resultados

def getResultadoIndividual (id,nome):
 url = "http://transparencia.gov.br/servidores/Servidor-DetalhaServidor.asp?IdServidor="+id
 f = urllib.urlopen(url).read().decode("ISO-8859-1")
 entrada = []
 tagsParaExclusao = ["</div>","</table>","</tr>","<tr >","<td class=\"firstChild\">","</td>","</a>","<td style=\"text-align: left;\">","<td style=\"text-align: right;\">","<tr  class=\"linhaPar\" >","<td><a href=\"Servidor-DetalhaServidor.asp?IdServidor=","<script type=\"text/javascript\" language=\"javascript\" src=\"../../Recursos/helper.js\"></script>"]
 return DecodificaCPF(f[f.find("<nobr> CPF:")+100:f.find("<nobr> CPF:")+130].strip(),nome)


def getAllResultados (nome,permiteDecodificacao,nPaginas=0):
 resultados = []
 if nPaginas<=0:
  nPaginas = getQtdePaginas(nome)
  nPaginas = nPaginas if nPaginas>1 else 2
 print("Processando " + str(nPaginas) + " paginas...")
 pbar = ProgressBar()
 for i in pbar(range (1,nPaginas)):
  resultados.append(getResultadosPorPagina(nome,i,permiteDecodificacao))
 return resultados


tokens = [("--id","Especifica o id do servidor na Transparencia do Governo"),("--nome","Especifica o nome do servidor na Transparencia do Governo"),("--help","Exibe esta mensagem de ajuda")]

def msgAjuda ():
 print("Uso: " + os.path.basename(__file__) + " [argumentos]\n")
 for token in tokens:
  print (token[0] + "\t" + token[1])
 return 0

def main (argv):
 if len(argv)==0:
  msgAjuda()
 else:
  entrada = [argv[0].replace("--id=",""),argv[1].replace("--nome=","")]
  print(getResultadoIndividual(entrada[0],entrada[1]))

if __name__ == "__main__":
 main(sys.argv[1:])
