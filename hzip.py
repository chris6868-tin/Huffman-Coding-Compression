import heapq
import pickle
import os
from collections import defaultdict, Counter

class Node:
    """Lớp đại diện cho một node trong cây Huffman"""
    def __init__(self, char=None, freq=0, left=None, right=None):
        self.char = char      # Ký tự (chỉ có ở lá)
        self.freq = freq      # Tần suất xuất hiện
        self.left = left      # Con trái
        self.right = right    # Con phải
    
    def __lt__(self, other):
        """So sánh để sử dụng trong heap"""
        return self.freq < other.freq

class HuffmanCoding:
    """Lớp chính xử lý nén và giải nén Huffman"""
    
    def __init__(self):
        self.root = None
        self.codes = {}
        
    def _build_frequency_table(self, data):
        """Xây dựng bảng tần suất các ký tự"""
        return Counter(data)
    
    def _build_huffman_tree(self, freq_table):
        """Xây dựng cây Huffman từ bảng tần suất"""
        if not freq_table:
            return None
            
        # Tạo heap các node lá
        heap = []
        for char, freq in freq_table.items():
            node = Node(char=char, freq=freq)
            heapq.heappush(heap, node)
        
        # Trường hợp đặc biệt: chỉ có 1 ký tự
        if len(heap) == 1:
            root = Node(freq=heap[0].freq)
            root.left = heapq.heappop(heap)
            return root
        
        # Xây dựng cây Huffman
        while len(heap) > 1:
            left = heapq.heappop(heap)
            right = heapq.heappop(heap)
            
            merged = Node(freq=left.freq + right.freq, left=left, right=right)
            heapq.heappush(heap, merged)
        
        return heap[0]
    
    def _build_codes(self, root):
        """Xây dựng mã Huffman cho các ký tự"""
        if not root:
            return {}
        
        codes = {}
        
        def dfs(node, code=""):
            if node.char is not None:  # Lá
                codes[node.char] = code if code else "0"  # Trường hợp chỉ có 1 ký tự
            else:
                if node.left:
                    dfs(node.left, code + "0")
                if node.right:
                    dfs(node.right, code + "1")
        
        dfs(root)
        return codes
    
    def _encode_data(self, data, codes):
        """Mã hóa dữ liệu thành chuỗi bit"""
        return ''.join(codes[char] for char in data)
    
    def _decode_data(self, encoded_data, root):
        """Giải mã chuỗi bit thành dữ liệu gốc"""
        if not root or not encoded_data:
            return b""
        
        decoded = []
        current = root
        
        for bit in encoded_data:
            if current.char is not None:  # Đến lá
                decoded.append(current.char)
                current = root
            
            if bit == '0':
                current = current.left
            else:
                current = current.right
        
        # Xử lý ký tự cuối cùng
        if current.char is not None:
            decoded.append(current.char)
        
        return bytes(decoded)
    
    def _serialize_tree(self, node):
        """Chuyển đổi cây thành dạng có thể lưu trữ hiệu quả"""
        if node is None:
            return None
        if node.char is not None:  # Lá
            return ('leaf', node.char)
        else:  # Node trong
            return ('internal', self._serialize_tree(node.left), self._serialize_tree(node.right))
    
    def _deserialize_tree(self, data):
        """Khôi phục cây từ dữ liệu đã serialize"""
        if data is None:
            return None
        if data[0] == 'leaf':
            return Node(char=data[1], freq=0)
        else:  # internal
            left = self._deserialize_tree(data[1])
            right = self._deserialize_tree(data[2])
            return Node(freq=0, left=left, right=right)

    def compress(self, input_file, output_file):
        """Nén file đầu vào"""
        try:
            # Đọc file đầu vào
            with open(input_file, 'rb') as f:
                data = f.read()
            
            if not data:
                print("File đầu vào trống!")
                return False
            
            print(f"Kích thước file gốc: {len(data)} bytes")
            
            # Xây dựng cây Huffman
            freq_table = self._build_frequency_table(data)
            self.root = self._build_huffman_tree(freq_table)
            self.codes = self._build_codes(self.root)
            
            # Mã hóa dữ liệu
            encoded_data = self._encode_data(data, self.codes)
            
            # Chuyển chuỗi bit thành bytes
            padding = 8 - len(encoded_data) % 8
            if padding != 8:
                encoded_data += '0' * padding
            
            compressed_data = bytearray()
            for i in range(0, len(encoded_data), 8):
                byte = encoded_data[i:i+8]
                compressed_data.append(int(byte, 2))
            
            # Lưu file nén với format tối ưu
            with open(output_file, 'wb') as f:
                # Lưu thông tin header
                import struct
                
                # Magic number để xác định file hzip
                f.write(b'HZIP')
                
                # Serialize cây Huffman
                tree_data = self._serialize_tree(self.root)
                tree_bytes = pickle.dumps(tree_data)
                
                # Lưu kích thước tree, padding và dữ liệu
                f.write(struct.pack('<I', len(tree_bytes)))  # Kích thước tree
                f.write(struct.pack('<B', padding))          # Padding
                f.write(tree_bytes)                          # Tree data
                f.write(bytes(compressed_data))              # Compressed data
            
            compressed_size = os.path.getsize(output_file)
            compression_ratio = (compressed_size / len(data)) * 100
            
            print(f"Kích thước file nén: {compressed_size} bytes")
            print(f"Tỷ lệ nén: {compression_ratio:.2f}%")
            
            if compression_ratio < 100:
                print(f"Tiết kiệm: {len(data) - compressed_size} bytes ({100 - compression_ratio:.2f}%)")
            else:
                print(f"Tăng: {compressed_size - len(data)} bytes (+{compression_ratio - 100:.2f}%)")
                print("(Với file nhỏ, metadata có thể lớn hơn dữ liệu)")
            
            return True
            
        except Exception as e:
            print(f"Lỗi khi nén file: {e}")
            return False
    
    def decompress(self, input_file, output_file):
        """Giải nén file"""
        try:
            # Đọc file nén
            with open(input_file, 'rb') as f:
                import struct
                
                # Kiểm tra magic number
                magic = f.read(4)
                if magic != b'HZIP':
                    print("Lỗi: File không phải định dạng HZIP!")
                    return False
                
                # Đọc header
                tree_size = struct.unpack('<I', f.read(4))[0]
                padding = struct.unpack('<B', f.read(1))[0]
                
                # Đọc tree data
                tree_bytes = f.read(tree_size)
                tree_data = pickle.loads(tree_bytes)
                self.root = self._deserialize_tree(tree_data)
                
                # Đọc compressed data
                compressed_data = f.read()
            
            # Chuyển bytes thành chuỗi bit
            encoded_data = ''.join(format(byte, '08b') for byte in compressed_data)
            
            # Loại bỏ padding
            if padding != 8:
                encoded_data = encoded_data[:-padding]
            
            # Giải mã
            decoded_data = self._decode_data(encoded_data, self.root)
            
            # Lưu file giải nén
            with open(output_file, 'wb') as f:
                f.write(decoded_data)
            
            print(f"Giải nén thành công! File đầu ra: {output_file}")
            print(f"Kích thước file giải nén: {len(decoded_data)} bytes")
            
            return True
            
        except Exception as e:
            print(f"Lỗi khi giải nén file: {e}")
            return False

def main():
    """Hàm chính của chương trình"""
    huffman = HuffmanCoding()
    
    print("=" * 50)
    print("CHƯƠNG TRÌNH HZIP - NÉN VÀ GIẢI NÉN FILE")
    print("Sử dụng thuật toán Huffman Coding")
    print("=" * 50)
    
    while True:
        print("\nChọn chế độ hoạt động:")
        print("1. Nén file")
        print("2. Giải nén file")
        print("3. Thoát")
        
        choice = input("\nNhập lựa chọn (1-3): ").strip()
        
        if choice == '1':
            input_file = input("Nhập đường dẫn file cần nén: ").strip()
            
            if not os.path.exists(input_file):
                print("File không tồn tại!")
                continue
            
            # Tạo tên file đầu ra
            base_name = os.path.splitext(input_file)[0]
            output_file = base_name + ".hzip"
            
            print(f"\nĐang nén file '{input_file}'...")
            if huffman.compress(input_file, output_file):
                print(f"Nén thành công! File nén: {output_file}")
            
        elif choice == '2':
            input_file = input("Nhập đường dẫn file cần giải nén (.hzip): ").strip()
            
            if not os.path.exists(input_file):
                print("File không tồn tại!")
                continue
            
            if not input_file.endswith('.hzip'):
                print("File phải có đuôi .hzip!")
                continue
            
            # Tạo tên file đầu ra
            output_file = input_file.replace('.hzip', '_decompressed')
            
            print(f"\nĐang giải nén file '{input_file}'...")
            if huffman.decompress(input_file, output_file):
                print("Giải nén hoàn tất!")
            
        elif choice == '3':
            print("Thoát chương trình. Tạm biệt!")
            break
            
        else:
            print("Lựa chọn không hợp lệ! Vui lòng chọn 1, 2 hoặc 3.")

if __name__ == "__main__":
    main()