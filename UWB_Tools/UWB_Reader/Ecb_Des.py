from Crypto.Cipher import DES, DES3
from Crypto.Util.Padding import pad, unpad

class MyEcbDes:
    def __init__(self):
        pass

    def des_encrypt(self, key, plaintext):
        cipher = DES.new(key, DES.MODE_ECB)
        padded_plaintext = pad(plaintext, DES.block_size)
        ciphertext = cipher.encrypt(padded_plaintext)
        return ciphertext

    def des_decrypt(self, key, ciphertext):
        cipher = DES.new(key, DES.MODE_ECB)
        padded_plaintext = cipher.decrypt(ciphertext)
        plaintext = unpad(padded_plaintext, DES.block_size)
        return plaintext

    def des3_encrypt(self, key, plaintext):
        cipher = DES3.new(key, DES3.MODE_ECB)
        padded_text = pad(plaintext, DES3.block_size)
        return cipher.encrypt(padded_text)

    def des3_decrypt(self, key, ciphertext):
        cipher = DES3.new(key, DES3.MODE_ECB)
        decrypted_padded_text = cipher.decrypt(ciphertext)
        return unpad(decrypted_padded_text, DES3.block_size)
    
    def str_xor(self, s1, s2):
        bytes1 = bytes.fromhex(s1)
        bytes2 = bytes.fromhex(s2)
        xor_result = bytes(a ^ b for a, b in zip(bytes1, bytes2))
        return xor_result.hex().upper()

    def xor_arrays(self, a, b):
        return bytes([x ^ y for x, y in zip(a, b)])
    
    def process_macdata(self, key, macdata):
        iv = b'\x00' * 8
        des = bytearray(8)
        num_blocks = len(macdata) // 8
        for i in range(num_blocks):
            part = macdata[i * 8:(i + 1) * 8]
            if i == 0:
                part = self.xor_arrays(part, iv)
                des[:] = self.des_encrypt(key, part)
            else:
                part = self.xor_arrays(des, part)
                des[:] = self.des_encrypt(key, part)
        return bytes(des)

if __name__ == '__main__':
    key = 'B6E6AB003A9455A3'
    plaintext = 'F9350143053F0001'
    crypto_helper = MyEcbDes(key)

    ciphertext = crypto_helper.des_encrypt(plaintext)
    print(f"Ciphertext: {ciphertext}")
    decrypted_text = crypto_helper.des_decrypt(ciphertext)
    print(f"Decrypted text: {decrypted_text}")

    plaintext = 'F9350143053F0001'
    crypto_helper.key = bytes.fromhex('B6E6AB003A9455A33DBE8869ECC59BE9')

    ciphertext = crypto_helper.des3_encrypt(plaintext)
    print(f"Ciphertext: {ciphertext}")
    decrypted_text = crypto_helper.des3_decrypt(ciphertext)
    print(f"Decrypted text: {decrypted_text}")