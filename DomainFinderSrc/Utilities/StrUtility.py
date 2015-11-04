table_name_alphanum_str = frozenset(
    "_abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ01234567890/ ")
table_name_alphanum_bytes = frozenset(
    b"_abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ01234567890/ ")


class StrUtility:
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