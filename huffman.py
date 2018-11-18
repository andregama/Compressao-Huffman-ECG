#! /usr/bin/env python
# coding: utf-8

import heapq, os, sys
from bitstring import BitArray

class HeapNo:
	def __init__(self, char, freq):
		self.char = char
		self.freq = freq
		self.esq = None
		self.dir = None

	def __lt__(self, other): #define a função No1 < No2 para os HeapNo
		if(other == None):
			return -1
		if(not isinstance(other, HeapNo)):
			return -1
		return self.freq > other.freq


class Huffman:
	def __init__(self, path):
		self.path = path
		self.heap = []
		self.codigos = {}
		self.mapReverso = {}

	# funcoes para Compressão:

	def make_freq_dict(self, texto): #criar o dicionario de frequencias de caracteres
		freq = {}
		for char in texto:
			if not char in freq:
				freq[char] = 0
			freq[char] += 1
		return freq

	def make_heap(self, freq): #criar uma lista de nos (caracter, frequencia) ordenada em ordem crescente pela frequencia
		for key in freq:
			no = HeapNo(key, freq[key]) #criar um no com o caracter e sua frequencia
			heapq.heappush(self.heap, no) #coloca o no na pilha (lista)

	def merge_nos(self): #criar a arvore de huffman unindo pares de nos com menores frequencias
		while(len(self.heap)>1):
			no1 = heapq.heappop(self.heap) #tira os dois nos com menores frequencias da pilha
			no2 = heapq.heappop(self.heap)

			merged = HeapNo(None, no1.freq + no2.freq) #une os nos somando a frequencia de ambos e guarda os nos "filhos" em esq e dir
			merged.esq = no1
			merged.dir = no2

			heapq.heappush(self.heap, merged)


	def criar_codigos_rec(self, raiz, noAtual):
		if(raiz == None): #se nao tem caracter, retorna
			return

		if(raiz.char != None): #se o no tem um caracter
			self.codigos[raiz.char] = noAtual #coloca no dicionario de codigos o codigo do no atual; a chave eh o caracter do no
			self.mapReverso[noAtual] = raiz.char
			return

		self.criar_codigos_rec(raiz.esq, noAtual + "0") #chama a funcao pros filhos esquerdo e direito, colocando mais um 0 no codigo pro filho esquerdo e 1 pro direito
		self.criar_codigos_rec(raiz.dir, noAtual + "1")


	def criar_codigos(self): #cria um código binario pra cada caracter na pilha
		raiz = heapq.heappop(self.heap)
		noAtual = ""
		self.criar_codigos_rec(raiz, noAtual) #chama a funcao recursiva


	def get_texto_codificado(self, texto): #cria o texto codificado
		texto_cod = ""
		for char in texto:
			texto_cod += self.codigos[char]
		return texto_cod

	def add_dict_codigos(self, texto_cod):
		texto=""
		for key in self.codigos:
			texto+=BitArray(key.encode()).bin
			texto+=BitArray(u"\u2980".encode()).bin
			texto+=self.codigos[key]
			texto+=BitArray(u"\u2980".encode()).bin
		texto_cod = texto + texto_cod
		return texto_cod

	def preenche_texto_cod(self, texto_cod): #preenche o texto com zeros pra ser multiplo de 8 e guarda os bits preenchidos no comeco do texto
		preenchimento = 8 - len(texto_cod) % 8
		for i in range(preenchimento):
			texto_cod += "0"

		preenche_info = "{0:08b}".format(preenchimento)
		texto_cod = preenche_info + texto_cod
		return texto_cod


	def get_byte_array(self, texto_cod_preenchido): #cria uma array de bytes a partir do texto codificado e preenchido
		if(len(texto_cod_preenchido) % 8 != 0):
			print("Texto não devidamente codificado")
			exit(0)

		b=bytearray()
		for i in range(0, len(texto_cod_preenchido), 8):
			byte = texto_cod_preenchido[i:i+8]
			b+=int(byte, 2).to_bytes(1,sys.byteorder) #transforma os bits em um numero inteiro e adiciona na bytearray
		return b


	def comprimir(self):
		nome_arquivo, ext_arquivo = os.path.splitext(self.path)
		arquivo_saida = nome_arquivo + ".bin"

		with open(nome_arquivo+ext_arquivo, 'r+') as arquivo, open(arquivo_saida, 'wb') as saida:
			texto = arquivo.read()
			texto = texto.rstrip() #tira os caracteres em branco no final do texto

			freq = self.make_freq_dict(texto)
			self.make_heap(freq)
			self.merge_nos()
			self.criar_codigos()

			texto_cod = self.get_texto_codificado(texto)
			texto_cod = self.add_dict_codigos(texto_cod)
			texto_cod_preenchido = self.preenche_texto_cod(texto_cod)

			b = self.get_byte_array(texto_cod_preenchido)
			saida.write(bytes(b))

		print("Compressão finalizada com sucesso!")

		return arquivo_saida


	""" funções para descompressão: """

	def remove_preenchimento(self, texto_cod_preenchido):
		preenche_info = texto_cod_preenchido[:8]
		preenchimento = int(preenche_info, 2)

		texto_cod_preenchido = texto_cod_preenchido[8:] #"exclui" o texto sobre a informacao de preenchimento
		texto_cod = texto_cod_preenchido[:-1*preenchimento]  #exclui os bits de preenchimento no final do texto

		return texto_cod

	def construir_dict_codigos(self, texto_cod):
		byte=""
		tam=0
		chars = texto_cod.split("111000101010011010000000") #cria uma lista com os caracteres dividos por este numero binario que funciona como separador
		chars.pop() #remove o ultimo elemento da lista
		for i in range(0, len(chars), 2):
			tam+=(len(chars[i])+len(chars[i+1])+48)
			self.mapReverso[chars[i+1]]=BitArray('0b' + chars[i]).tobytes().decode()
		texto_cod = texto_cod[tam:] #remove os caracteres usados para construir o dicionario
		return  texto_cod

	def decodificar_texto(self, texto_cod):
		noAtual = ""
		texto_decod = ""

		for bit in texto_cod:
			noAtual += bit
			if(noAtual in self.mapReverso):
				char = self.mapReverso[noAtual]
				texto_decod += char
				noAtual = ""

		return texto_decod


	def descomprimir(self):
		nome_arquivo, ext_arquivo = os.path.splitext(self.path)
		arquivo_saida = nome_arquivo + "_descomprimido" + ".txt"
		arquivo_entrada = nome_arquivo+ ext_arquivo

		with open(arquivo_entrada, 'rb') as arquivo, open(arquivo_saida, 'w') as saida:
			bit_string = ""

            #abaixo os bytes sao convertidos em uma string de bits
			byte = arquivo.read(1) #le o primeiro byte do arquivo
			while byte:
				num=int.from_bytes(byte,sys.byteorder) #transforma o byte em um numero inteiro
				bits="{0:b}".format(num).rjust(8, '0') #converte o codigo para binario e preenche com zeros na esquerda até completar 8 bits
				bit_string += bits #guarda os bits em bit_string
				byte = arquivo.read(1)

			texto_cod = self.remove_preenchimento(bit_string)
			texto_cod = self.construir_dict_codigos(texto_cod)
			descomprimido_texto = self.decodificar_texto(texto_cod)

			saida.write(descomprimido_texto)

		print("Descompressão finalizada com sucesso!")
		return arquivo_saida


a=Huffman('C:/Users/andre/Desktop/ReadMeh.bin')
#a.comprimir()
a.descomprimir()
