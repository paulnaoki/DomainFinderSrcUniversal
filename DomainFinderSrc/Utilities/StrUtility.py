from Crypto.Cipher import XOR
import base64


table_name_alphanum_str = frozenset(
    "_abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ01234567890/ ")
table_name_alphanum_bytes = frozenset(
    b"_abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ01234567890/ ")


class StrUtility:
    @staticmethod
    def convert_str_to_array(data_str: str, separator=',') -> list:
        assert separator is not None, "separator cannot be None."
        if len(data_str) == 0:
            return []
        else:
            return data_str.split(separator)

    @staticmethod
    def convert_array_to_str(data_list: list, separator=',') -> str:
        assert separator is not None, "separator cannot be None."
        if isinstance(data_list, str):
            return data_list
        if len(data_list) == 0:
            return ""
        else:
            return separator.join([str(x) for x in data_list])

    @staticmethod
    def escape(pattern, alphanum_str, alphanum_bytes):
        """
        Escape all the characters in pattern except ASCII letters, numbers and '_'.
        """
        if isinstance(pattern, str):
            alphanum = alphanum_str
            s = list(pattern)
            for i, c in enumerate(pattern):
                if c not in alphanum:
                    if c == "\000":
                        s[i] = "\\000"
                    else:
                        s[i] = "\\" + c
            return "".join(s)
        else:
            alphanum = alphanum_bytes
            s = []
            esc = ord(b"\\")
            for c in pattern:
                if c in alphanum:
                    s.append(c)
                else:
                    if c == 0:
                        s.extend(b"\\000")
                    else:
                        s.append(esc)
                        s.append(c)
            return bytes(s)

    @staticmethod
    def make_valid_table_name(table_name: str) -> str:
        if len(table_name) == 0:
            return "no_name"
        else:
            return table_name.replace("'", "''")
            # return StrUtility.escape(table_name, table_name_alphanum_str, table_name_alphanum_bytes)

    @staticmethod
    def encrypt_XOR(key: str, plaintext: str) -> str:
        cipher = XOR.new(key)
        return str(base64.b64encode(cipher.encrypt(plaintext)), encoding='utf-8')

    @staticmethod
    def decrypt_XOR(key: str, ciphertext: str) -> str:
        ciphertext = ciphertext.encode(encoding='utf-8')
        cipher = XOR.new(key)
        return str(cipher.decrypt(base64.b64decode(ciphertext)), encoding='utf-8')