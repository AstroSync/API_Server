import ctypes

crc_table: list[int] = [0x00000000, 0x04C11DB7, 0x09823B6E, 0x0D4326D9, 0x130476DC, 0x17C56B6B, 0x1A864DB2, 0x1E475005,
                        0x2608EDB8, 0x22C9F00F, 0x2F8AD6D6, 0x2B4BCB61,  0x350C9B64, 0x31CD86D3, 0x3C8EA00A, 0x384FBDBD]


def calculate_crc(crc: int, data: list[int]):
    for word in data:
        crc = (crc ^ word) & 0xffffffff
        # print(f'CRC: {crc=:#04x} data: {word:#04x}')
        for _ in range(8):
            crc = ((crc << 4) ^ crc_table[crc >> 28]) & 0xffffffff
    return crc


def init_crc(board_time: int) -> int:
    crc = (-1 ^ (board_time ^ 0x01041964)) & 0xffffffff
    for _ in range(8):
        crc = ((crc << 4) ^ crc_table[crc >> 28]) & 0xffffffff
    return crc


class BRK_Radio_Frame_VarID(ctypes.LittleEndianStructure):
    _fields_: list = [('res', ctypes.c_uint32, 3),
                      ('offset', ctypes.c_uint32, 21),
                      ('var_id', ctypes.c_uint32, 4),
                      ('dev_id', ctypes.c_uint32, 4)]

    def __init__(self, dev_id: int, var_id: int, offset: int, *args, **kw):
        self._fields_.append(('data', ctypes.c_uint32, 32))
        super().__init__(*args, **kw)
        self.offset = offset
        self.dev_id = dev_id
        self.var_id = var_id
        self.res = 0


def calc_size(val: int):
    size = 0
    while val > 0:
        val = val >> 8
        size += 1
    return size & 0xff


def calculate_write_var_header(data_list: tuple[list[BRK_Radio_Frame_VarID], list[int]], board_time: int):
    """data_list: [(BRK_Radio_Frame_VarID, data_value), ...]"""
    values_list: list[int] = data_list[1]
    var_id_list: list[BRK_Radio_Frame_VarID] = data_list[0]
    values_len_list: list[int] = [calc_size(value) for value in values_list]
    values_bytes_list = [value.to_bytes(data_len, 'little') for value, data_len in zip(values_list, values_len_list)]
    msg = b''.join([bytes(var_id) + value_len.to_bytes(1, 'big') + value
                    for var_id, value_len, value in zip(var_id_list, values_len_list, values_bytes_list)])
    msg += (0).to_bytes(4, 'big')
    val = len(msg) % 4
    msg += (0).to_bytes(4 - val if val > 0 else val, 'big')
    # print(f'{int.from_bytes(msg, "big"):#10x}')
    words = [int.from_bytes(reversed(msg[i:i+4]), 'big') for i in range(0, len(msg), 4)]
    crc = calculate_crc(init_crc(board_time), words)
    msg += crc.to_bytes(4, 'little')
    return msg


def calculate_read_var_header(data_list: tuple[list[BRK_Radio_Frame_VarID], list[int]]):
    """data_list: [(BRK_Radio_Frame_VarID, length)]"""
    msg = b''.join([bytes(var_id) + length.to_bytes(1, 'big') for var_id, length in zip(data_list[0], data_list[1])])
    msg += (0).to_bytes(4, 'big')
    pad = len(msg) % 4
    msg += (0).to_bytes(4 - pad if pad > 0 else pad, 'big')
    return msg


if __name__ == '__main__':
    frame = BRK_Radio_Frame_VarID(6, 5, 4)
    # print(f'{int.from_bytes(bytes(frame), byteorder="little"):#04x}')
    # print(calc_size(0x1212121212121212))
    read_data = calculate_write_var_header(([BRK_Radio_Frame_VarID(6, 5, 4),
                                             BRK_Radio_Frame_VarID(6, 5, 4)], [0x0201, 0x0201]), 1234)
    write_data = calculate_read_var_header(([BRK_Radio_Frame_VarID(6, 5, 4)], [0x02]))
    print(f'{int.from_bytes(read_data, byteorder="big"):#07x}')
    print(f'{int.from_bytes(write_data, byteorder="big"):#07x}')
    # print(f'{ctypes.cast(ctypes.pointer(frame), ctypes.POINTER(ctypes.c_uint32)).contents.value:#04x}')
    # init_crc = init_crc(1234)
    # print(f'{init_crc=:#04x}')
    # arr1 = [0x65000020, 0x00020102, 0x00000000]
    # print(f'crc={calculate_crc(init_crc, arr1):#04x}')
    # print(f'crc={calculate_crc(0x280d97b6, arr1):#04x}')
