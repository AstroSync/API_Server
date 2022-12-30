from __future__ import annotations
import os
import numpy as np
import pandas as pd


class Singleton(type):
    _instances: dict = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class FrameFormats(metaclass=Singleton):
    def __init__(self) -> None:
        self.tmi: list[pd.DataFrame] = [pd.read_csv(os.path.join(os.path.dirname(__file__),
                                                                 f'NORBI_TMI_formats/tmi{i}.csv')) for i in range(0, 9)]

    def get_tmi(self, tmi_num: int) -> pd.DataFrame:
        return self.tmi[tmi_num]

tmi_formats: FrameFormats = FrameFormats()

class RadioPacket:
    """ NORBI radio packet of transport layer

    | Packet length | RX ADDR | TX ADDR | Transaction number |   Res   | Message ID |   Payload   |  CRC16  |
    |:-------------:|:-------:|:-------:|:------------------:|:-------:|:----------:|:-----------:|:-------:|
    |     1 byte    | 4 bytes | 4 bytes |       2 bytes      | 2 bytes |   2 bytes  | < 240 bytes | 2 bytes |

    Returns:
        _type_: _description_
    """
    __frame_length_offset: int = 0
    __frame_length_size: int = 1
    __tx_address_offset: int = 1
    __tx_address_size: int = 4
    __rx_address_offset: int = 5
    __rx_address_size: int = 4
    __transaction_number_offset: int = 9
    __transaction_number_size: int = 2
    __msg_id_offset: int = 13
    __msg_id_size: int = 2
    __msg_offset: int = 15
    __crc_size: int = 2

    raw_data_len: int
    frame_length: int
    tx_address: bytes
    rx_address: bytes
    msg_id: int
    transaction_number: int
    msg: bytes
    crc16: bytes

    def __init__(self, raw_data: bytes) -> None:
        self.raw_data_len = len(raw_data)
        self.frame_length = int.from_bytes(raw_data[self.__frame_length_offset:self.__frame_length_offset + self.__frame_length_size], 'big')
        self.tx_address = raw_data[self.__tx_address_offset:self.__tx_address_offset + self.__tx_address_size]
        self.rx_address = raw_data[self.__rx_address_offset:self.__rx_address_offset + self.__rx_address_size]
        self.msg_id = int.from_bytes(raw_data[self.__msg_id_offset:self.__msg_id_offset + self.__msg_id_size], 'big')
        self.transaction_number = int.from_bytes(raw_data[self.__transaction_number_offset: self.__transaction_number_offset + self.__transaction_number_size], 'big')
        self.msg = raw_data[self.__msg_offset: -(self.__crc_size)]
        self.crc16 = raw_data[self.raw_data_len - self.__crc_size:]

    def Msg(self) -> bytes:
        return self.msg

    def MsgID(self) -> int:
        return self.msg_id

    def CRC16(self) -> bytes:
        return self.crc16

    @staticmethod
    def address_to_string(address: bytes) -> str:
        return f'{address[0]}.{address[1]}.{address[2]}.{address[3]}'

    def __repr__(self):
        return f'Frame length: {self.frame_length}\nTX Address: {self.address_to_string(self.tx_address)}\n' \
               f'RX Address: {self.address_to_string(self.rx_address)}\nTransaction number: {self.transaction_number}' \
               f'\nMsg ID: {self.msg_id},\nMsg: {list(bytearray(self.msg))}\n'\
               f'CRC16: 0x{int.from_bytes(self.crc16, "big"):02X}\n'


def frame_parser(data: bytes) -> tuple[RadioPacket, pd.DataFrame]:
    radio_frame: RadioPacket = RadioPacket(data)
    tmi_num: int = radio_frame.MsgID() // 2 - 1 if radio_frame.MsgID() > 0 else 0
    tmi: pd.DataFrame = tmi_formats.get_tmi(tmi_num=tmi_num).reset_index(drop=True)
    new_header_name: str = f'Параметры ТМИ {tmi_num if radio_frame.MsgID() != 0 else "0 (Маяк)"}'
    tmi_frame: pd.DataFrame = tmi.rename(columns={'Параметр': new_header_name})
    tmi_sizes: list[int] = tmi['Размер Байт'].to_numpy(np.int32).tolist()
    msg_data: list[bytes] = split_data_by_sizes(radio_frame.Msg(), tmi_sizes)
    tmi_frame['Значения'] = pd.Series(msg_data)  # add column
    for index, row in tmi_frame.iterrows():
        if row['Значения'] is not np.nan:
            if 'int' in row['Тип данных']:
                tmi_frame.at[index, 'Значения'] = int.from_bytes(row['Значения'], 'little')
            elif row['Тип данных'] == 'string':
                tmi_frame.at[index, 'Значения'] = row['Значения'].decode("ascii")
            elif row['Тип данных'] == 'hex':
                tmi_frame.at[index, 'Значения'] = f"0x{int.from_bytes(row['Значения'], 'little'):X}"
    tmi_frame.at[len(tmi_frame) - 1, 'Значения'] = f"0x{int.from_bytes(radio_frame.CRC16(), 'little'):02X}"
    return radio_frame, tmi_frame


def split_data_by_sizes(msg: bytes, field_sizes: list[int]) -> list[bytes]:
    return [msg[sum(field_sizes[:i]):sum(field_sizes[:i]) + field_size] for i, field_size in enumerate(field_sizes)]


# def get_tmi_offsets(tmi_num: int) -> tuple[pd.DataFrame, int, int]:
#     tmi = tmi_formats.get_tmi(tmi_num)[4:-1]
#     tmi_offsets = tmi[tmi['OffSet VarID5'].notnull()].sort_values('OffSet VarID5')
#     tmi_sizes = tmi_offsets['Размер Байт'].to_numpy(np.int32)
#     first_offset = tmi_offsets['OffSet VarID5'].iloc[0]
#     size = int(sum(tmi_sizes))
#     return tmi_offsets, first_offset, size


def convert_to_bytes(data: str | list, separator=' ') -> bytes:
    converted_data = b''
    if len(data) == 0:
        return b''
    try:
        if isinstance(data, str):
            converted_data = bytes([int(x, 16) for x in data.split(separator)])
        elif isinstance(data[0], int):
            converted_data = bytes(data)
        elif isinstance(data[0], str):
            converted_data = bytes([int(x, 16) for x in data])
    except TypeError as err:
        print(err)
        return b''
    return converted_data



if __name__ == '__main__':
    frame: str = '8E FF FF FF FF A 6 1 FB A A6 0 0 0 0 F1 F 0 0 94 F 36 94 2 0 42 52 4B 20 4D 57 ' \
                 '20 56 45 52 3A 30 35 61 5F 30 32 61 0 0 0 0 E 1 0 E7 8 0 0 0 2 25 0 A C1 A 7E ' \
                 'F2 4B 2 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 ' \
                 '0 0 0 0 0 0 0 0 0 0 0 0 0 80 0 0 0 0 6C 1E 1 0 1 F 3 0 15 0 53 4 7A 2 1B 1B 1B 0 ' \
                 'A1 0 DF 1E 4E E8'
    df_frame = frame_parser(convert_to_bytes(frame))[1]
    print(df_frame)
    # print(df_frame)
    # print(get_tmi_frame(0))
    # print(get_tmi_offsets(8))
    # for i in range(0, 9):
    #     print(get_tmi_offsets(i)[0].to_csv(f'./tmi{i}.csv', sep=',', encoding='utf-8-sig', index=False))
    # data = get_tmi_offsets(5)
    # print([data[0][:15], *data[0][15:]])
    # print([data[1][:15].sum(), *data[1][15:]])
    # print(tmi8_optimizer(data[0], data[1]))
    # print(df[(df['ТМИ 0'].notnull())])
