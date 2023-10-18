import os
import struct
from pathlib import Path


class ArchiveHeader:
    def __init__(self, signature, version, compression_algorithm, error_protection, original_length, num_files):
        self.signature = signature
        self.version = version
        self.compression_algorithm = compression_algorithm
        self.error_protection = error_protection
        self.original_length = original_length
        self.num_files = num_files
        self.file_info = []

    def add_file_info(self, filename, file_size):
        self.file_info.append((filename, file_size))

    def serialize(self):
        header_data = struct.pack('4s B 2s 4s B B', self.signature, self.version, self.compression_algorithm,
                                  self.error_protection, self.original_length, self.num_files)
        for filename, file_size in self.file_info:
            filename_encoded = filename.encode('utf-8')
            header_data += struct.pack('I', len(filename_encoded)) + filename_encoded + struct.pack('Q', file_size)
        return header_data

    @classmethod
    def deserialize(cls, data):
        signature, version, compression_algorithm, error_protection, original_length, num_files = struct.unpack(
            '4s B 2s 4s B B', data[:13])
        archive_header = cls(signature, version, compression_algorithm, error_protection, original_length, num_files)
        return archive_header


class ArchiveCodec:
    def encode(self, filenames, archive_path):
        archive_header = ArchiveHeader(b'MYFM', 1, b'00', b'00', 0, len(filenames))

        for file in filenames:
            filename = file.name
            file_size = os.path.getsize(file)
            archive_header.add_file_info(filename, file_size)

        # Сериализация заголовка
        header_data = archive_header.serialize()

        with open(archive_path, 'wb') as archive:
            archive.write(header_data)

            # Добавление содержимое файлов
            for filename, _ in archive_header.file_info:
                file_path = Path(os.getcwd(), filename)
                with open(file_path, 'rb') as source_file:
                    archive.write(source_file.read())

    def decode(self, archive_path, output_directory):
        with open(archive_path, 'rb') as archive:
            header_data = archive.read(13)
            archive_header = ArchiveHeader.deserialize(header_data)
            our_signature = archive_header.signature.decode('utf-8')
            if our_signature != 'MYFM' or archive_header.compression_algorithm != b'00':
                print("Invalid archive signature.")
                return

            filenames = []
            sizes = []
            for _ in range(archive_header.num_files):
                header_data = archive.read(4)
                filename_length = struct.unpack('I', header_data[:4])[0]
                header_data = archive.read(filename_length)
                filename = header_data[:filename_length].decode('utf-8')
                header_data = archive.read(8)
                file_size = struct.unpack('Q', header_data[:8])[0]
                archive_header.add_file_info(filename, file_size)
                filenames.append(filename)
                sizes.append(file_size)

            for i in range(len(filenames)):
                with open(Path(output_directory, filenames[i]), 'wb') as file:
                    file.write(archive.read(sizes[i]))


if __name__ == "__main__":
    with open('binary_file.bin', 'wb') as file:
        data = b'\x01\x02\x03\x04\x05'
        file.write(data)

    filenames = [Path(os.getcwd(), 'file_1.txt'),
                 Path(os.getcwd(), 'binary_file.bin')]

    codec = ArchiveCodec()
    codec.encode(filenames=filenames, archive_path=Path(os.getcwd(), 'arch.MYFM'))
    codec.decode(archive_path=Path(os.getcwd(), 'arch.MYFM'), output_directory=Path(os.getcwd()))