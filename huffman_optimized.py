import heapq
import os
import struct
from collections import defaultdict
from typing import Dict, Tuple, Optional


class HuffmanNode:
    __slots__ = ('char', 'freq', 'left', 'right')
    def __init__(self, char: Optional[str] = None, freq: int = 0,
                 left: Optional['HuffmanNode'] = None,
                 right: Optional['HuffmanNode'] = None):
        self.char = char
        self.freq = freq
        self.left = left
        self.right = right

    def __lt__(self, other: 'HuffmanNode') -> bool:
        return self.freq < other.freq



class HuffmanCoder:
    def __init__(self):
        self._codebook: Dict[str, str] = {}
        self._tree: Optional[HuffmanNode] = None

    def _build_frequency_table(self, data: str) -> Dict[str, int]:
        frequency = defaultdict(int)
        for char in data:
            frequency[char] += 1
        return frequency

    def _build_huffman_tree(self, frequency: Dict[str, int]) -> HuffmanNode:
        nodes = [HuffmanNode(char=char, freq=freq) for char, freq in frequency.items()]
        heapq.heapify(nodes)

        while len(nodes) > 1:
            left = heapq.heappop(nodes)
            right = heapq.heappop(nodes)
            merged = HuffmanNode(freq=left.freq + right.freq, left=left, right=right)
            heapq.heappush(nodes, merged)

        return nodes[0] if nodes else HuffmanNode()

    def _build_codebook(self) -> None:
        if not self._tree:
            return
        stack = [(self._tree, "")]
        while stack:
            node, code = stack.pop()
            if node.char is not None:
                self._codebook[node.char] = code
            else:
                if node.right:
                    stack.append((node.right, code + "1"))
                if node.left:
                    stack.append((node.left, code + "0"))

    def encode(self, data: str) -> Tuple[str, Dict[str, int]]:
        if not data:
            return "", {}

        frequency = self._build_frequency_table(data)
        self._tree = self._build_huffman_tree(frequency)
        self._codebook = {}
        self._build_codebook()

        return ''.join(self._codebook[char] for char in data), frequency

    def decode(self, encoded_data: str) -> str:
        if not encoded_data or not self._tree:
            return ""


        decoded_data = []
        current_node = self._tree
        for bit in encoded_data:
            current_node = current_node.left if bit == '0' else current_node.right
            if current_node.char is not None:
                decoded_data.append(current_node.char)
                current_node = self._tree
        return ''.join(decoded_data)


def read_file(filename: str) -> str:
    """Lecture d'un fichier"""
    if not os.path.exists(filename):
        raise FileNotFoundError(f"Le fichier {filename} n'existe pas !")

    with open(filename, 'r', encoding='utf-8') as file:
        return file.read()


def write_file(filename: str, content: str) -> None:
    """Écriture dans un fichier"""
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(content) 


def save_compressed(output_file: str, encoded_data: str, frequency: Dict[str, int]) -> None:
    padding = 8 - len(encoded_data) % 8 if len(encoded_data) % 8 != 0 else 0
    padded_data = encoded_data + '0' * padding
    bytes_data = bytes(int(padded_data[i:i+8], 2) for i in range(0, len(padded_data), 8))
    
    with open(output_file, 'wb') as file:
        file.write(struct.pack('>I', len(frequency)))
        file.write(struct.pack('B', padding))
        for char, freq in frequency.items():
            # Pack character as 2-byte UTF-16 and frequency as 4-byte unsigned int
            file.write(struct.pack('>H', ord(char)))  # 2 bytes for character
            file.write(struct.pack('>I', freq))       # 4 bytes for frequency
        file.write(bytes_data)

def load_compressed(input_file: str) -> Tuple[str, Dict[str, int]]:
    with open(input_file, 'rb') as file:
        num_symbols = struct.unpack('>I', file.read(4))[0]
        padding = struct.unpack('B', file.read(1))[0]
        
        frequency = {}
        for _ in range(num_symbols):
            # Read 2-byte UTF-16 code point and convert to character
            char = chr(struct.unpack('>H', file.read(2))[0])
            frequency[char] = struct.unpack('>I', file.read(4))[0]
        
        bytes_data = file.read()
        bit_string = ''.join(format(byte, '08b') for byte in bytes_data)
        
        if padding > 0:
            bit_string = bit_string[:-padding]
    
    return bit_string, frequency


def compress_file(input_file: str, output_file: str) -> None:
    """Compression d'un fichier"""
    data = read_file(input_file)
    coder = HuffmanCoder()
    encoded_data, frequency = coder.encode(data)
    
    # Sauvegarder les données compressées
    save_compressed(output_file, encoded_data, frequency)
    
    # Afficher les informations de compression
    original_size = os.path.getsize(input_file)
    compressed_size = os.path.getsize(output_file)
    compression_ratio = original_size / compressed_size if compressed_size > 0 else 0
    
    print(f"Taille originale : {original_size} octets")
    print(f"Taille compressée : {compressed_size} octets")
    print(f"Ratio de compression : {compression_ratio:.2f}x")


def decompress_file(input_file: str, output_file: str) -> None:
    """Décompression d'un fichier"""
    encoded_data, frequency = load_compressed(input_file)
    
    coder = HuffmanCoder()
    # Reconstruire l'arbre de Huffman à partir de la table de fréquences
    coder._tree = coder._build_huffman_tree(frequency)
    
    # Décoder les données
    decoded_data = coder.decode(encoded_data)
    
    # Sauvegarder les données décompressées
    write_file(output_file, decoded_data)
    
    print(f"Décodage terminé. Vérifiez le fichier : {output_file}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Codage et décodage de Huffman')
    parser.add_argument('mode', choices=['encode', 'decode'], help='Mode de fonctionnement : encode ou decode')
    parser.add_argument('input_file', help='Fichier d\'entrée')
    parser.add_argument('output_file', help='Fichier de sortie')

    args = parser.parse_args()

    if args.mode == 'encode':
        compress_file(args.input_file, args.output_file)
    else:
        decompress_file(args.input_file, args.output_file)


if __name__ == "__main__":
    main()